import json
import time

from src.application.factories.agent_factory import AgentBuilder
from src.domain.config import STANDARD_SCENARIO
from src.domain.constants import MODELS_TO_TEST, SYSTEM_PROMPT
from src.infrastructure.evaluation import evaluate_quality, extract_invoice_json
from src.infrastructure.metrics_service import MetricsService

GRAY = "\033[90m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

class BenchmarkRunner:
    @staticmethod
    def run_scenario(model: str, debug: bool = False):
        print(f"\n[URUCHAMIANIE] Model: {model} | Framework: Baseline-Python\n")

        agent = AgentBuilder.build(model)
        client = agent["client"]
        tools_schema = agent["tools_schema"]
        available_tools = agent["available_tools"]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        metrics = MetricsService(model=model)
        metrics.sample_ram()

        for index, user_text in enumerate(STANDARD_SCENARIO):
            print(f"\n[Wiadomość {index + 1}/{len(STANDARD_SCENARIO)}]")
            print(f"Użytkownik: {user_text[:80]}{'...' if len(user_text) > 80 else ''}")

            metrics.log_turn("user", user_text)
            messages.append({"role": "user", "content": user_text})
            turn_start = time.perf_counter()
            metrics.sample_ram()

            agent_response = ""
            tool_calls_this_turn = []

            if debug:
                print(f"  {GRAY}[DEBUG] Czekam na odpowiedź agenta...{RESET}")

            while True:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools_schema,
                    )
                except Exception as error:
                    print(f"{RED}[BŁĄD OLLAMY]: {error}{RESET}")
                    print("Upewnij się, że serwer Ollama działa i masz pobrany ten model (ollama run model_name).")
                    return

                usage = response.usage
                tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
                tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0
                metrics.record_llm_call(tokens_in=tokens_in, tokens_out=tokens_out)
                metrics.record_first_response()
                metrics.sample_ram()

                message = response.choices[0].message
                messages.append(message.model_dump())

                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        tool_calls_this_turn.append(func_name)
                        if debug:
                            print(f"\n  {YELLOW}[DEBUG] Agent wywołuje narzędzie: {func_name}{RESET}")

                        try:
                            args = json.loads(tool_call.function.arguments)

                            if func_name == "calculate_line":
                                if "qty" in args and "quantity" not in args:
                                    args["quantity"] = args.pop("qty")
                                if "price" in args and "unit_price_net" not in args:
                                    args["unit_price_net"] = args.pop("price")
                                if "net_price" in args and "unit_price_net" not in args:
                                    args["unit_price_net"] = args.pop("net_price")
                                if "quantity" not in args and "qty" not in args:
                                    args["quantity"] = args.get("amount", 0)

                            result = available_tools[func_name](**args)

                            if debug:
                                print(f"  {GRAY}[DEBUG] Wynik narzędzia {func_name}: {result}{RESET}")

                            if func_name == "format_invoice" and isinstance(result, dict):
                                metrics.final_invoice_json = result
                                agent_response = json.dumps(result, ensure_ascii=False)

                        except Exception as error:
                            result = {"error": str(error)}
                            if debug:
                                print(f"  {RED}[DEBUG ERROR] {error}{RESET}")

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )

                    continue

                if debug and message.content:
                    print(f"  {GRAY}[DEBUG] Agent: {message.content}{RESET}")

                agent_response = message.content or ""
                break

            turn_time = round(time.perf_counter() - turn_start, 3)
            preview = agent_response[:120] + ("..." if len(agent_response) > 120 else "")

            if not debug:
                print(f"Agent: {preview}")
                print(f"[{turn_time}s | użyte narzędzia: {tool_calls_this_turn}]")
            else:
                print(f"\n  {GREEN}[ZAKOŃCZONO TURĘ w {turn_time}s. Narzędzia: {tool_calls_this_turn}]{RESET}")

            metrics.log_turn(
                "agent",
                agent_response,
                {
                    "turn_time_s": turn_time,
                    "tool_calls": tool_calls_this_turn,
                },
            )

            if '"invoice"' in agent_response and not metrics.final_invoice_json:
                metrics.final_invoice_json = extract_invoice_json(agent_response)

        metrics.finish()
        metrics.quality = evaluate_quality(metrics.conversation_log)
        saved_path = metrics.save()

        summary = metrics.to_dict()
        print(
            f"\n[PODSUMOWANIE {model}] Czas: {summary['total_time_s']}s | "
            f"Ocena: {metrics.quality.get('auto_score_0_5')}/5"
        )
        print(f"Zapisano w: {saved_path.name}")

    @classmethod
    def execute_all(cls, debug: bool = False):
        for model in MODELS_TO_TEST:
            cls.run_scenario(model, debug=debug)
