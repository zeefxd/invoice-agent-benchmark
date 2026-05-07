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

    println("Wybierz model do uruchomienia")
    var model = readln()

    if (model.isEmpty()) {
        println("No model given, fallback to gemma4:e4b")
        model = "gemma4:e4b"
    }

    runBlocking {
        try {

            val model = LLModel(
                provider = LLMProvider.Ollama,
                id = model,
//                contextLength = 4096
            )

            val agent = AIAgent(
                promptExecutor = simpleOllamaAIExecutor(),
                systemPrompt = SystemPrompt,
                llmModel = model,
                temperature = 0.3,
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
                    onAgentStarting { ctx ->
                        println("Starting ${ctx.agent.agentConfig.model.id}, ${ctx.runId}")
                    }
                    onAgentClosing { println("Closing $it") }
                    onToolCallCompleted { eventContext ->
                        println("Tool finished: ${eventContext.toolName} with args ${eventContext.toolArgs}, output: ${eventContext.toolResult}")
                    }
                    onToolCallStarting { eventContext ->
                        println("Tool started: ${eventContext.toolName} with args ${eventContext.toolArgs}")
                    }
                    onToolCallFailed { eventContext ->
                        println("Tool failed: ${eventContext.toolName} failed ${eventContext.error?.message}, cause: ${eventContext.error?.cause}, " )
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