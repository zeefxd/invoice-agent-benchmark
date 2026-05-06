package org.example

import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.dsl.builder.node
import ai.koog.agents.core.dsl.builder.strategy
import ai.koog.agents.core.dsl.extension.nodeLLMRequest
import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.features.eventHandler.feature.handleEvents
import ai.koog.prompt.executor.llms.MultiLLMPromptExecutor
import ai.koog.prompt.executor.llms.all.simpleOllamaAIExecutor
import ai.koog.prompt.executor.ollama.client.OllamaClient
import ai.koog.prompt.llm.LLMProvider
import ai.koog.prompt.llm.LLModel
import ai.koog.prompt.message.Message
import ai.koog.prompt.streaming.StreamFrame
import ai.koog.prompt.structure.json.JsonStructure
import ai.koog.prompt.structure.json.generator.BasicJsonSchemaGenerator
import kotlinx.coroutines.runBlocking
import org.example.tools.Address
import org.example.tools.InvoiceItem
import org.example.tools.InvoiceMeta
import org.example.tools.InvoiceOutput
import org.example.tools.InvoiceTotalResult
import org.example.tools.NIP
import org.example.tools.Participant
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
    val exampleInvoice = listOf(
        InvoiceOutput(
            invoice = InvoiceMeta(
                issueDate = "2026-05-06",
                saleDate = "2026-05-05",
                paymentDueDate = "2026-05-20",
                paymentMethod = "Przelew",
                bankAccount = "12 3456 7890 1234 5678 9012 3456"
            ), seller =
                Participant(
                name = "Firma XYZ Sp. z o.o.", nip = NIP("123-456-78-90"), address = Address(
                    street = "ul. Kwiatowa 10", postalCode = "30-001", city = "Kraków"
                )
            ), buyer = Participant(
                name = "ABC Solutions Sp. z o.o.", nip = NIP("987-654-32-10"), address = Address(
                    street = "ul. Słoneczna 5", postalCode = "33-300", city = "Nowy Sącz"
                )
            ), lineItems = listOf(
                InvoiceItem(
                    name = "Usługa programistyczna",
                    quantity = 10.0,
                    unit = "h",
                    unitPriceNet = 150.0,
                    vatRate = "23%",
                    vatAmount = 345.0,
                    netTotal = 1500.0,
                    grossTotal = 1845.0,
                ), InvoiceItem(
                    name = "Konsultacje IT",
                    quantity = 5.0,
                    unit = "h",
                    unitPriceNet = 200.0,
                    vatRate = "23%",
                    netTotal = 1000.0,
                    vatAmount = 230.0,
                    grossTotal = 1230.0
                )
            ), totals = InvoiceTotalResult(
                net = 2500.0,
                vat = 575.0,
                gross = 3075.0,
            )
        )
    )


    runBlocking {
        try {

            val model = LLModel(
                provider = LLMProvider.Ollama,
//                "gemma4:e4b",
//                "gemma4:26b",
                id = "gpt-oss:20b",
//                id = "qwen3.5:9b",
//                contextLength = 4096
            )

//            val client = OllamaClient()
//            val exec = MultiLLMPromptExecutor(client)


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