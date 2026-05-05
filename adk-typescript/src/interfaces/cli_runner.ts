import { Runner, InMemorySessionService } from '@google/adk';
import { buildAgent } from '../application/factories/agent_factory';
import { StandardScenario } from '../domain/config';
import { ModelsToTest } from '../domain/constants';
import { MetricsService } from '../infrastructure/metrics_service';
import { extractInvoiceJson, evaluateQuality } from '../infrastructure/evaluation';

export async function runScenario(modelName: string, debug: boolean) {
    console.log(`[URUCHAMIANIE] Model: ${modelName} | Framework: ADK-TypeScript`);

    const metrics = new MetricsService(modelName);
    metrics.sampleRam();

    let agent;
    try {
        agent = buildAgent(modelName);
    } catch (err) {
        console.error(`Błąd budowania agenta: ${err}`);
        return;
    }

    const sessionService = new InMemorySessionService();
    const runner = new Runner({
        appName: "invoice-benchmark",
        agent: agent,
        sessionService: sessionService,
    });

    const session = await sessionService.createSession({ userId: "bench-user", appName: "invoice-benchmark" } as any);
    const sessionId = session.id;

    for (let i = 0; i < StandardScenario.length; i++) {
        const userText = StandardScenario[i];
        console.log(`\n[Wiadomość ${i + 1}/${StandardScenario.length}]`);
        
        let preview = userText;
        if (preview.length > 80) preview = preview.substring(0, 80) + "...";
        console.log(`Użytkownik: ${preview}`);

        metrics.logTurn("user", userText, null);
        const turnStart = Date.now();
        metrics.sampleRam();

        let agentResponse = "";
        let toolCallsThisTurn: string[] = [];

        if (debug) {
            console.log("  \x1b[90m[DEBUG] Czekam na odpowiedź agenta...\x1b[0m");
        }

        let tokensIn = 0;
        let tokensOut = 0;
        let firstResponseRecorded = false;

        try {
            const stream = await runner.runAsync({
                userId: "bench-user", 
                sessionId: sessionId, 
                newMessage: { role: "user", parts: [{ text: userText }] }
            });

            for await (const evt of stream) {
                if (!firstResponseRecorded) {
                    metrics.recordFirstResponse();
                    firstResponseRecorded = true;
                }
                const event = evt as any;

                if (event.content?.parts) {
                    for (const part of event.content.parts) {
                        if (part.text) {
                            if (debug) {
                                process.stdout.write(`\x1b[90m${part.text}\x1b[0m`);
                            }
                            agentResponse += part.text;
                        }
                        if (part.functionCall) {
                            toolCallsThisTurn.push(part.functionCall.name);
                            if (debug) {
                                console.log(`\n  \x1b[93m[DEBUG] Agent wywołuje narzędzie: ${part.functionCall.name}\x1b[0m`);
                            }
                        }
                    }
                }

                if (event.usageMetadata) {
                    tokensIn = event.usageMetadata.promptTokens || 0;
                    tokensOut = event.usageMetadata.candidatesTokenCount || event.usageMetadata.completionTokens || 0;
                }
            }
        } catch (err: any) {
            if (debug) {
                console.log(`\n  \x1b[91m[DEBUG ERROR] ${err.message || err}\x1b[0m`);
            }
            if (String(err).includes("Tool") || String(err).includes("not found")) {
                agentResponse = "[BŁĄD: model wywołał nieistniejące narzędzie]";
                toolCallsThisTurn.push("HALLUCINATED_TOOL");
                metrics.recordLlmCall(0, 0);
                if (!firstResponseRecorded) {
                    metrics.recordFirstResponse();
                    firstResponseRecorded = true;
                }
            } else {
                throw err;
            }
        }

        if (debug) {
            console.log("");
        }

        metrics.recordLlmCall(tokensIn, tokensOut);
        metrics.sampleRam();

        const turnTime = (Date.now() - turnStart) / 1000.0;

        if (agentResponse.includes('"invoice"') && (agentResponse.includes('"totals"') || agentResponse.includes('"financials"'))) {
            const extracted = extractInvoiceJson(agentResponse);
            if (extracted) {
                metrics.finalInvoiceJson = extracted;
            }
        }

        if (!debug) {
            let respPreview = agentResponse;
            if (respPreview.length > 120) respPreview = respPreview.substring(0, 120) + "...";
            console.log(`Agent: ${respPreview}`);
            console.log(`[${turnTime.toFixed(3)}s | użyte narzędzia: [${toolCallsThisTurn.join(", ")}]]`);
        } else {
            console.log(`\n  \x1b[92m[ZAKOŃCZONO TURĘ w ${turnTime.toFixed(3)}s. Narzędzia: [${toolCallsThisTurn.join(", ")}]]\x1b[0m`);
        }

        metrics.logTurn("agent", agentResponse, {
            turn_time_s: turnTime,
            tool_calls: toolCallsThisTurn
        });
    }

    metrics.finish();
    metrics.quality = evaluateQuality(metrics.conversationLog);
    const savedPath = metrics.save();

    const dict = metrics.toDict();
    let score = dict.quality && dict.quality.auto_score_0_5 ? dict.quality.auto_score_0_5 : 0.0;
    
    console.log(`\n[PODSUMOWANIE ${modelName}] Czas: ${dict.total_time_s.toFixed(3)}s | Ocena: ${score.toFixed(2)}/5`);
    console.log(`Zapisano w: ${savedPath}`);
}

export async function executeAll(debug: boolean) {
    for (const model of ModelsToTest) {
        await runScenario(model, debug);
    }
}
