package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import kotlin.math.round

@Serializable
data class InvoiceLineResult(
    val netTotal: Double,
    val vatAmount: Double,
    val grossTotal: Double,
    val error: String
)

@Tool("calculate_line")
@LLMDescription("Oblicza wartości netto, VAT i brutto dla jednej pozycji faktury")
fun calculateLine(
    @LLMDescription("Ilość")
    quantity: Double,
    @LLMDescription("Cena netto za jednostkę")
    unitPriceNet: Double,
    @LLMDescription("Stawka VAT jako string, np. \"23%\", \"8%\", \"5%\", \"0%\", \"zw.\".")
    vatRate: String
): InvoiceLineResult {
    val rates = mapOf(
        "23%" to 0.23,
        "8%" to 0.08,
        "5%" to 0.05,
        "0%" to 0.0,
        "zw." to 0.0
    )

    val key = vatRate.lowercase().replace(" ", "")
    val rate = rates.getOrElse(key) {
        return InvoiceLineResult(
            netTotal = 0.0,
            vatAmount = 0.0,
            grossTotal = 0.0,
            error = "Nieznana stawka VAT jako string $key. Dozwolone: ${rates.entries.joinToString()}"
        )
    }

    val netTotal = quantity * unitPriceNet
    val vatAmount = netTotal * rate
    val grossTotal = netTotal + vatAmount

    return InvoiceLineResult(
        netTotal = round(netTotal * 100) / 100.0,
        vatAmount = round(vatAmount * 100) / 100.0,
        grossTotal = round(grossTotal * 100) / 100.0,
        error = ""
    )
}