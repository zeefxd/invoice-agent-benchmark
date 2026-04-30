import asyncio
import time
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from src.domain.constants import MODELS_TO_TEST
from src.domain.config import STANDARD_SCENARIO
from src.application.factories.agent_factory import AgentBuilder
from src.infrastructure.metrics_service import MetricsService
from src.infrastructure.evaluation import extract_invoice_json, evaluate_quality

class BenchmarkRunner:
    @staticmethod
    async def run_scenario(model: str, debug: bool = False):
        print(f"\n[URUCHAMIANIE] Model: {model} | Framework: ADK-Python\n")
        
        metrics = MetricsService(model=model)
        metrics.sample_ram()
        
        agent = AgentBuilder.build(model)
        runner = InMemoryRunner(agent=agent, app_name="invoice-benchmark")
        session = await runner.session_service.create_session(app_name="invoice-benchmark", user_id="bench-user")
        
        for i, user_text in enumerate(STANDARD_SCENARIO):
            print(f"\n[Wiadomość {i + 1}/{len(STANDARD_SCENARIO)}]")
            print(f"Użytkownik: {user_text[:80]}{'...' if len(user_text) > 80 else ''}")
            
            metrics.log_turn("user", user_text)
            msg = Content(role="user", parts=[Part(text=user_text)])
            turn_start = time.perf_counter()
            metrics.sample_ram()
            
            agent_response = ""
            tool_calls_this_turn =[]

            if debug:
                print("  \033[90m[DEBUG] Czekam na odpowiedź agenta...\033[0m")

            try:
                async for event in runner.run_async(user_id="bench-user", session_id=session.id, new_message=msg):
                    
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            
                            is_tool_call = False
                            tool_name = "unknown"
                            
                            if hasattr(part, "function_call") and part.function_call:
                                is_tool_call = True
                                tool_name = getattr(part.function_call, "name", "unknown")
                                
                            elif hasattr(part, "tool_call") and part.tool_call:
                                is_tool_call = True
                                tool_name = getattr(part.tool_call, "name", "unknown")

                            if is_tool_call:
                                tool_calls_this_turn.append(tool_name)
                                if debug:
                                    print(f"\n  \033[93m[DEBUG] Agent wywołuje narzędzie: {tool_name}\033[0m")

                            elif debug and hasattr(part, "text") and part.text:
                                print(f"\033[90m{part.text}\033[0m", end="", flush=True)

                    if event.is_final_response():
                        if debug:
                            print()
                            
                        if event.content and event.content.parts:
                            agent_response = "".join(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
                        
                        tokens_in, tokens_out = 0, 0
                        if hasattr(event, "usage_metadata") and event.usage_metadata:
                            um = event.usage_metadata
                            tokens_in = getattr(um, "prompt_token_count", 0) or getattr(um, "input_tokens", 0) or 0
                            tokens_out = getattr(um, "candidates_token_count", 0) or getattr(um, "output_tokens", 0) or 0
                        
                        metrics.record_llm_call(tokens_in=tokens_in, tokens_out=tokens_out)
                        metrics.record_first_response()
                        metrics.sample_ram()
                        
            except ValueError as e:
                err_msg = str(e)
                if debug:
                    print(f"\n  \033[91m[DEBUG ERROR] {err_msg}\033[0m")
                    
                if "not found" in err_msg and "Tool" in err_msg:
                    agent_response = f"[BŁĄD: model wywołał nieistniejące narzędzie]"
                    tool_calls_this_turn.append("HALLUCINATED_TOOL")
                    metrics.record_llm_call()
                    metrics.record_first_response()
                else:
                    raise

            turn_time = round(time.perf_counter() - turn_start, 3)
            preview = agent_response[:120] + ("..." if len(agent_response) > 120 else "")
            
            if not debug:
                print(f"Agent: {preview}")
                print(f"[{turn_time}s | użyte narzędzia: {tool_calls_this_turn}]")
            else:
                print(f"\n  \033[92m[ZAKOŃCZONO TURĘ w {turn_time}s. Narzędzia: {tool_calls_this_turn}]\033[0m")

            metrics.log_turn("agent", agent_response, {
                "turn_time_s": turn_time,
                "tool_calls": tool_calls_this_turn,
            })

            if '"invoice"' in agent_response:
                metrics.final_invoice_json = extract_invoice_json(agent_response)

        metrics.finish()
        metrics.quality = evaluate_quality(metrics.conversation_log)
        saved_path = metrics.save()
        
        print(f"\n[PODSUMOWANIE {model}] Czas: {metrics.to_dict()['total_time_s']}s | Ocena: {metrics.quality.get('auto_score_0_5')}/5")
        print(f"Zapisano w: {saved_path.name}")

    @classmethod
    def execute_all(cls, debug: bool = False):
        for model in MODELS_TO_TEST:
            asyncio.run(cls.run_scenario(model, debug=debug))