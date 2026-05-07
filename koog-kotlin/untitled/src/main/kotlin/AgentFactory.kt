package org.example.application.factories

import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.agent.singleRunStrategy
import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.features.eventHandler.feature.handleEvents
import ai.koog.prompt.executor.llms.all.simpleOllamaAIExecutor
import ai.koog.prompt.llm.LLMProvider
import ai.koog.prompt.llm.LLModel
import org.example.domain.INVOICE_AGENT_SYSTEM_PROMPT
import org.example.tools.*

object AgentFactory {
    fun build(modelId: String): AIAgent<String, String> {
        val model = LLModel(
            provider = LLMProvider.Ollama,
            id = modelId
        )

        return AIAgent<String, String>(
            promptExecutor = simpleOllamaAIExecutor(),
            systemPrompt = INVOICE_AGENT_SYSTEM_PROMPT,
            strategy = singleRunStrategy(),
            llmModel = model,
            temperature = 0.3,
            toolRegistry = ToolRegistry {
                tool(::askUser)
                tool(::validateNIP)
                tool(::calculateLine)
                tool(::calculateTotals)
                tool(::formatInvoice)
            }
        ) {
            handleEvents {
                onAgentStarting { ctx ->
                    println("Starting agent: ${ctx.agent.agentConfig.model.id}, Run ID: ${ctx.runId}")
                }
                onAgentClosing {
                    println("Agent session closed.")
                }
                onToolCallStarting { eventContext ->
                    println("Tool started: ${eventContext.toolName} with args ${eventContext.toolArgs}")
                }
                onToolCallCompleted { eventContext ->
                    println("Tool finished: ${eventContext.toolName}, result: ${eventContext.toolResult}")
                }
                onToolCallFailed { eventContext ->
                    println("Tool failed: ${eventContext.toolName}, error: ${eventContext.error?.message}")
                }
            }
        }
    }
}