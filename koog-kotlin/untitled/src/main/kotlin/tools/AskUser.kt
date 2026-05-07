package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool

@Tool
@LLMDescription("Ask the user a question by sending it to stdout and return the answer from stdin")
fun askUser(
    @LLMDescription("Question from the agent") question: String
): String {
    println(question)
    val scriptedAnswer = ScriptedAnswers.nextOrNull()
    if (scriptedAnswer != null) {
        println(scriptedAnswer)
        return scriptedAnswer
    }
    return readln()
}
