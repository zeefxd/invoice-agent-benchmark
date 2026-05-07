package org.example.interfaces

import org.example.application.factories.AgentFactory
import org.example.domain.MODELS_TO_TEST
import org.example.domain.STANDARD_SCENARIO
import org.example.infrastructure.evaluateQuality
import org.example.infrastructure.extractInvoiceJson
import org.example.infrastructure.MetricsService
import org.example.tools.ScriptedAnswers

object CliRunner {
    suspend fun executeAll(debug: Boolean) {
        for (model in MODELS_TO_TEST) {
            println("[URUCHAMIANIE] Model: $model | Framework: Koog-Kotlin")
            val agent = AgentFactory.build(model)

            val metrics = MetricsService(model)
            metrics.sampleRam()

            ScriptedAnswers.load(STANDARD_SCENARIO.drop(1))
            metrics.logTurn("user", STANDARD_SCENARIO.first())

            val response = agent.run(STANDARD_SCENARIO.first())

            metrics.logTurn("agent", response)
            metrics.finalInvoiceJson = extractInvoiceJson(response)
            metrics.quality = evaluateQuality(response)
            metrics.finish()
            metrics.save()

            println(response)
            if (debug) {
                println("[DEBUG] Zakonczono uruchomienie dla $model")
            }
        }
    }
}
