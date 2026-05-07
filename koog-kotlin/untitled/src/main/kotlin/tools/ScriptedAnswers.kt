package org.example.tools

object ScriptedAnswers {
    private val answers = ArrayDeque<String>()

    fun load(nextAnswers: List<String>) {
        answers.clear()
        answers.addAll(nextAnswers)
    }

    fun nextOrNull(): String? {
        return if (answers.isEmpty()) null else answers.removeFirst()
    }
}
