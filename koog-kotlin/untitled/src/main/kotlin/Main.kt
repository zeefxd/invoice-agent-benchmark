package org.example

import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.features.eventHandler.feature.handleEvents
import ai.koog.prompt.executor.llms.all.simpleOllamaAIExecutor
import ai.koog.prompt.llm.LLMProvider
import ai.koog.prompt.llm.LLModel
import kotlinx.coroutines.runBlocking
import org.example.tools.calculateLine
import org.example.tools.calculateTotals
import org.example.tools.formatInvoice
import org.example.tools.validateNIP

@Tool
@LLMDescription("Ask the user a question by sending it to stdout and return the answer from stdin")
fun askUser(
    @LLMDescription("Question from the agent") question: String
): String {
    println(question)
    return readln()
}


fun main() {
    runBlocking {
        try {

            val model = LLModel(
                LLMProvider.Ollama,
//                "gemma4:e4b"
//                "gemma4:26b"
//                "gpt-oss:20b",
                "qwen3.5:9b"

            )


            val agent = AIAgent(
                promptExecutor = simpleOllamaAIExecutor(),
                systemPrompt = SystemPrompt,
                llmModel = model,
                temperature = 0.7,
                toolRegistry = ToolRegistry {
                    tool(::askUser)
                    tool(::validateNIP)
                    tool(::calculateLine)
                    tool(::calculateTotals)
                    tool(::formatInvoice)
                },
//            maxIterations = 50
            ) {
                handleEvents {
                    onAgentStarting { println("Starting $it") }
                    onAgentClosing { println("Closing $it") }
                    onToolCallStarting { eventContext ->
                        println("Tool called: ${eventContext.toolName} with args ${eventContext.toolArgs}")
                    }

                }
            }

            val startingPrompt =
                "Chcę wystawić fakturę. Sprzedawca to Aperture Solutions sp. z o.o., NIP 5271234567, ul. Marszałkowska 10/4, 00-001 Warszawa. Faktura dla Jana Kowalskiego, NIP 8431234560, ul. Długa 3/4, 30-200 Kraków. Dwie pozycje: konsultacje IT — 40 godzin po 150 zł netto, VAT 23%, oraz licencja oprogramowania — 1 sztuka, 2500 zł netto, VAT 23%. Płatność przelewem na konto 12 3456 7890 1234 5678 9012 3456, termin 14 dni."
            println("Running prompt against ${model.id}: $startingPrompt")
            val resp = agent.run(startingPrompt)
            println(resp)
        } catch (e: Exception) {
            println(e)
        }
    }
}