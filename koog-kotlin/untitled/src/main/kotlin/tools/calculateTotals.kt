package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import kotlin.math.round

@Serializable
data class InvoiceTotalResult(
    val net: Double,
    val vat: Double,
    val gross: Double,
    val error: String? = null
)

@Tool("calculate_totals")
@LLMDescription("Oblicza sumy netto, VAT i brutto dla wszystkich pozycji faktury.")
fun calculateTotals(
    @LLMDescription("Lista pozycji na fakturze")
    lines: Array<InvoiceLineResult>
): InvoiceTotalResult {
    val netSum = lines.sumOf { it.netTotal }
    val vatSum = lines.sumOf { it.vatAmount }
    val grossSum = lines.sumOf { it.grossTotal }

    val net = round(netSum * 100) / 100
    val vat = round(vatSum * 100) / 100
    val gross = round(grossSum * 100) / 100

    val result =  InvoiceTotalResult(net = net, vat = vat, gross = gross, error = "")
    println("calculate_totals: $result")
    return result
}