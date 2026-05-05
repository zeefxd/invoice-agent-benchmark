package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import java.text.DateFormat
import java.util.Date

@Serializable
data class NIP(val value: String)

@Serializable
data class Address(
    val street: String,
    val postalCode: String,
    val city: String
)

@Serializable
data class Participant(
    val name: String,
    val nip: NIP,
    val address: Address
)

@Serializable
data class InvoiceMeta(
    val issueDate: String,
    val saleDate: String,
    val paymentDueDate: String,
    val paymentMethod: String,
    val bankAccount: String
)

@Serializable
data class InvoiceLineInput(
    val name: String,
    val quantity: Double = 0.0,
    val unit: String = "",
    val unitPriceNet: Double = 0.0,
    val vatRate: String = "23%"
)

@Serializable
data class InvoiceInput(
    val invoice: InvoiceMeta,
    val seller: Participant,
    val buyer: Participant,
    val lineItems: List<InvoiceLineInput>
)

@Serializable
data class InvoiceOutput(
    val invoice: InvoiceMeta,
    val seller: Participant,
    val buyer: Participant,
    val lineItems: List<InvoiceLineResult>,
    val totals: InvoiceTotalResult
)

@Tool("format_invoice")
@LLMDescription("Formatuje i zwraca gotowy JSON faktury VAT w restrykcyjnej strukturze.")
fun formatInvoice(
    data: InvoiceInput
): InvoiceOutput {

    val linesCalculated = mutableListOf<InvoiceLineResult>()

    for (item in data.lineItems) {
        val calc = calculateLine(
            quantity = item.quantity,
            unitPriceNet = item.unitPriceNet,
            vatRate = item.vatRate
        )

        if (calc.error.isNotBlank()) {
            throw IllegalArgumentException("Błąd w pozycji '${item.name}': ${calc.error}")
        }

        linesCalculated.add(
            InvoiceLineResult(
                netTotal = calc.netTotal,
                vatAmount = calc.vatAmount,
                grossTotal = calc.grossTotal,
                error = calc.error
            )
        )
    }

    val totals = calculateTotals(linesCalculated.toTypedArray())

    return InvoiceOutput(
        invoice = data.invoice,
        seller = data.seller,
        buyer = data.buyer,
        lineItems = linesCalculated,
        totals = totals
    )
}