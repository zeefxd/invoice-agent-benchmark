package interfaces

import (
    "context"
    "fmt"
    "strings"
    "time"

    "adk-benchmark/src/application/factories"
    "adk-benchmark/src/domain"
    "adk-benchmark/src/infrastructure"

    "google.golang.org/adk/agent"
    "google.golang.org/adk/runner"
    "google.golang.org/adk/session"
    "google.golang.org/genai"
)

func RunScenario(ctx context.Context, modelName string, debug bool) {
    fmt.Printf("[URUCHAMIANIE] Model: %s | Framework: ADK-Go\n", modelName)

    metrics := infrastructure.NewMetricsService(modelName)
    metrics.SampleRAM()

    ag, err := factories.BuildAgent(ctx, modelName)
    if err != nil {
        fmt.Printf("Błąd budowania agenta: %v\n", err)
        return
    }

    sessionService := session.InMemoryService()
    r, err := runner.New(runner.Config{
        AppName:        "invoice-benchmark",
        Agent:          ag,
        SessionService: sessionService,
    })
    if err != nil {
        fmt.Printf("Błąd tworzenia runnera: %v\n", err)
        return
    }

    respCreate, err := sessionService.Create(ctx, &session.CreateRequest{
        AppName: "invoice-benchmark",
        UserID:  "bench-user",
    })
    if err != nil {
        fmt.Printf("Błąd tworzenia sesji: %v\n", err)
        return
    }
    sessionID := respCreate.Session.ID()

    for i, userText := range domain.StandardScenario {
        fmt.Printf("\n[Wiadomość %d/%d]\n", i+1, len(domain.StandardScenario))

        preview := userText
        if len(preview) > 80 {
            preview = preview[:80] + "..."
        }
        fmt.Printf("Użytkownik: %s\n", preview)

        metrics.LogTurn("user", userText, nil)
        turnStart := time.Now()
        metrics.SampleRAM()

        agentResponse := ""
        toolCallsThisTurn := []string{}

        if debug {
            fmt.Println("  \033[90m[DEBUG] Czekam na odpowiedź agenta...\033[0m")
        }

        var content *genai.Content
        contentList := genai.Text(userText)
        if len(contentList) > 0 {
            content = contentList[0]
        }
        
        events := r.Run(ctx, "bench-user", sessionID, content, agent.RunConfig{})

        tokensIn, tokensOut := 0, 0
        firstResponseRecorded := false

        func() {
            defer func() {
                if p := recover(); p != nil {
                    errMsg := fmt.Sprintf("%v", p)
                    if debug {
                        fmt.Printf("\n  \033[91m[DEBUG ERROR] %s\033[0m\n", errMsg)
                    }
                    if strings.Contains(errMsg, "not found") && strings.Contains(errMsg, "Tool") {
                        agentResponse = "[BŁĄD: model wywołał nieistniejące narzędzie]"
                        toolCallsThisTurn = append(toolCallsThisTurn, "HALLUCINATED_TOOL")
                        metrics.RecordLLMCall(0, 0)
                        if !firstResponseRecorded {
                            metrics.RecordFirstResponse()
                            firstResponseRecorded = true
                        }
                    } else {
                        panic(p)
                    }
                }
            }()

            for event := range events {
			if event == nil {
				continue
			}

			if !firstResponseRecorded {
				metrics.RecordFirstResponse()
				firstResponseRecorded = true
			}

			if event.Content != nil {
				for _, part := range event.Content.Parts {
					if part == nil {
						continue
					}
					
					if part.Text != "" {
						if debug {
							fmt.Printf("\033[90m%s\033[0m", part.Text)
						}
						agentResponse += part.Text
					}
					
					if part.FunctionCall != nil {
						toolCallsThisTurn = append(toolCallsThisTurn, part.FunctionCall.Name)
						if debug {
							fmt.Printf("\n  \033[93m[DEBUG] Agent wywołuje narzędzie: %s\033[0m\n", part.FunctionCall.Name)
						}
					}
				}
			}

			if event.UsageMetadata != nil {
				tokensIn = int(event.UsageMetadata.PromptTokenCount)
				tokensOut = int(event.UsageMetadata.CandidatesTokenCount)
			}
		}
		}()

        if debug {
            fmt.Println()
        }

        metrics.RecordLLMCall(tokensIn, tokensOut)
        metrics.SampleRAM()  

        turnTime := time.Since(turnStart).Seconds()

		if strings.Contains(agentResponse, "\"invoice\"") && (strings.Contains(agentResponse, "\"totals\"") || strings.Contains(agentResponse, "\"financials\"")) {
			extracted := infrastructure.ExtractInvoiceJSON(agentResponse)
			if extracted != nil {
				metrics.FinalInvoiceJSON = extracted
			}
		}
        
        if !debug {
            respPreview := agentResponse
            if len(respPreview) > 120 {
                respPreview = respPreview[:120] + "..."
            }
            fmt.Printf("Agent: %s\n", respPreview)
            fmt.Printf("[%.3fs | użyte narzędzia: %v]\n", turnTime, toolCallsThisTurn)
        } else {
            fmt.Printf("\n  \033[92m[ZAKOŃCZONO TURĘ w %.3fs. Narzędzia: %v]\033[0m\n", turnTime, toolCallsThisTurn)
        }

        metrics.LogTurn("agent", agentResponse, map[string]any{
            "turn_time_s": turnTime,
            "tool_calls":  toolCallsThisTurn,
        })
    }

    metrics.Finish()
    metrics.Quality = infrastructure.EvaluateQuality(metrics.ConversationLog)
    savedPath := metrics.Save()

    dict := metrics.ToDict()
    score, ok := metrics.Quality["auto_score_0_5"].(float64)
    if !ok {
        score = 0.0
    }
    fmt.Printf("\n[PODSUMOWANIE %s] Czas: %.3fs | Ocena: %.2f/5\n", modelName, dict["total_time_s"], score)
    fmt.Printf("Zapisano w: %s\n", savedPath)
}

func ExecuteAll(debug bool) {
    ctx := context.Background()
    for _, model := range domain.ModelsToTest {
        RunScenario(ctx, model, debug)
    }
}