package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import kotlin.math.round

@Serializable
data class InvoiceLineResult(
    val net_total: Double,
    val vat_amount: Double,
    val gross_total: Double,
    val error: String? = null
)

@Tool("calculate_line")
@LLMDescription("Oblicza wartości netto, VAT i brutto dla jednej pozycji faktury")
fun calculateLine(
    @LLMDescription("Ilość") quantity: Double,
    @LLMDescription("Cena netto za jednostkę") unitPriceNet: Double,
    @LLMDescription("Stawka VAT jako string, np. \"23%\", \"8%\", \"5%\", \"0%\", \"zw.\".") vatRate: String
): InvoiceLineResult {
    val rates = mapOf(
        "23%" to 0.23, "8%" to 0.08, "5%" to 0.05, "0%" to 0.0, "zw." to 0.0
    )

    val key = vatRate.lowercase().replace(" ", "")
    val rate = rates.getOrElse(key) {
        return InvoiceLineResult(
            net_total = 0.0,
            vat_amount = 0.0,
            gross_total = 0.0,
            error = "Nieznana stawka VAT jako string $key. Dozwolone: ${rates.entries.joinToString()}"
        )
    }

    val netTotal = quantity * unitPriceNet
    val vatAmount = netTotal * rate
    val grossTotal = netTotal + vatAmount

    val result = InvoiceLineResult(
        net_total = round(netTotal * 100) / 100.0,
        vat_amount = round(vatAmount * 100) / 100.0,
        gross_total = round(grossTotal * 100) / 100.0,
    )

    println("calculate_line: $result")
    return result
}