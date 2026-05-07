package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import org.example.tools.InvoiceLineResult
import kotlin.math.round

@Serializable
data class InvoiceTotalResult(
    val net_total: Double,
    val vat_amount: Double,
    val gross_total: Double,
    val error: String? = null
)

@Tool("calculate_totals")
@LLMDescription("Oblicza sumy netto, VAT i brutto dla wszystkich pozycji faktury.")
fun calculateTotals(
    @LLMDescription("Lista pozycji na fakturze")
    lines: Array<InvoiceLineResult>
): InvoiceTotalResult {
    val netSum = lines.sumOf { it.net_total }
    val vatSum = lines.sumOf { it.vat_amount }
    val grossSum = lines.sumOf { it.gross_total }

    val net = round(netSum * 100) / 100
    val vat = round(vatSum * 100) / 100
    val gross = round(grossSum * 100) / 100

    val result =  InvoiceTotalResult(net_total = net, vat_amount = vat, gross_total = gross, error = "")
    println("calculate_totals: $result")
    return result
}