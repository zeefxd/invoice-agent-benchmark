package org.example

import ai.koog.agents.core.agent.functionalStrategy
import ai.koog.prompt.streaming.StreamFrame

val myStrategy = functionalStrategy<String, Unit> { input ->
    llm.writeSession {
        appendPrompt { user(input) }

        val stream = requestLLMStreaming()

        stream.collect { frame ->
            when (frame) {
                is StreamFrame.TextDelta -> print(frame.text)
//                is StreamFrame.ReasoningDelta -> print("[Reasoning] text=${frame.text} summary=${frame.summary}")
                is StreamFrame.ToolCallComplete -> {
                    println("\n🔧 Tool call: ${frame.name} args=${frame.content}")
                    // Optionally parse lazily:
                    // val json = frame.contentJson
                }

                is StreamFrame.End -> println("\n[END] reason=${frame.finishReason}")
                else -> {} // Handle other frame types (TextComplete, ToolCallDelta, etc.)
            }
        }
    }
//    input

//    val response = requestLLM(input)
//    response.asAssistantMessage().content
}
