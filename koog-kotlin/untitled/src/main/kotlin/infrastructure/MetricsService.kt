package org.example.infrastructure

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.time.Instant

import org.example.domain.RESULTS_DIR
import org.example.domain.SUMMARY_CSV_PATH
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject

class MetricsService(
    private val model: String,
    private val framework: String = "koog-kotlin"
) {
    private val startWall = System.nanoTime()
    private var endWall: Long? = null
    private val ramSamples = mutableListOf<Long>()
    private val conversationLog = mutableListOf<Map<String, Any?>>()
    var finalInvoiceJson: Any? = null
    var quality: Map<String, Any> = emptyMap()

    fun sampleRam() {
        val runtime = Runtime.getRuntime()
        val usedMb = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024
        ramSamples.add(usedMb)
    }

    fun logTurn(role: String, content: String, meta: Map<String, Any?> = emptyMap()) {
        conversationLog.add(
            mapOf(
                "turn" to conversationLog.size + 1,
                "role" to role,
                "content" to content.take(2000),
                "meta" to meta,
                "wall_offset_s" to ((System.nanoTime() - startWall) / 1_000_000_000.0),
            )
        )
    }

    fun finish() {
        endWall = System.nanoTime()
        sampleRam()
    }

    fun toDict(): Map<String, Any?> {
        val totalTimeS = ((endWall ?: System.nanoTime()) - startWall) / 1_000_000_000.0
        return mapOf(
            "timestamp" to Instant.now().toString(),
            "framework" to framework,
            "model" to model,
            "ttfr_s" to 0.0,
            "total_time_s" to totalTimeS,
            "llm_rounds" to 1,
            "tokens_input" to 0,
            "tokens_output" to 0,
            "tokens_total" to 0,
            "ram_peak_mb" to (ramSamples.maxOrNull() ?: 0),
            "quality" to quality,
            "final_invoice_json" to finalInvoiceJson,
            "conversation_log" to conversationLog,
        )
    }

    private fun Any?.toJsonElement(): JsonElement = when (this) {
        null -> JsonNull
        is String -> JsonPrimitive(this)
        is Number -> JsonPrimitive(this)
        is Boolean -> JsonPrimitive(this)
        is Map<*, *> -> buildJsonObject {
            for ((key, value) in this@toJsonElement) {
                put(key.toString(), value.toJsonElement())
            }
        }
        is Iterable<*> -> buildJsonArray {
            for (value in this@toJsonElement) {
                add(value.toJsonElement())
            }
        }
        is Array<*> -> buildJsonArray {
            for (value in this@toJsonElement) {
                add(value.toJsonElement())
            }
        }
        else -> JsonPrimitive(this.toString())
    }

    fun save(): java.nio.file.Path {
        Files.createDirectories(RESULTS_DIR)
        val slug = model.replace(Regex("[^\\w\\-]"), "-")
        val fileName = "${framework}_${slug}_${System.currentTimeMillis() / 1000}.json"
        val resultPath = RESULTS_DIR.resolve(fileName)

        val json = Json { prettyPrint = true }
        Files.writeString(resultPath, json.encodeToString(JsonElement.serializer(), toDict().toJsonElement()), StandardCharsets.UTF_8)

        if (!Files.exists(SUMMARY_CSV_PATH)) {
            Files.createDirectories(SUMMARY_CSV_PATH.parent)
            Files.writeString(
                SUMMARY_CSV_PATH,
                "framework,model,ttfr_s,total_time_s,llm_rounds,tokens_input,tokens_output,tokens_total,ram_peak_mb,auto_score,invoice_json_ok,timestamp\n",
                StandardCharsets.UTF_8
            )
        }

        val data = toDict()
        val qualityScore = (quality["auto_score_0_5"] ?: 0)
        val csvRow = listOf(
            data["framework"],
            data["model"],
            data["ttfr_s"],
            data["total_time_s"],
            data["llm_rounds"],
            data["tokens_input"],
            data["tokens_output"],
            data["tokens_total"],
            data["ram_peak_mb"],
            qualityScore,
            if (finalInvoiceJson != null) 1 else 0,
            data["timestamp"],
        ).joinToString(",")

        Files.writeString(
            SUMMARY_CSV_PATH,
            "$csvRow\n",
            StandardCharsets.UTF_8,
            java.nio.file.StandardOpenOption.APPEND
        )

        return resultPath
    }
}
