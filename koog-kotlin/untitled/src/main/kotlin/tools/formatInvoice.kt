package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class NIP(val value: String)

@Serializable
data class Address(
    val street: String, @SerialName("postal_code") val postalCode: String, val city: String
)

@Serializable
data class Participant(
    val name: String, val nip: NIP, val address: Address
)

@Serializable
data class InvoiceMeta(
    @SerialName("issue_date") val issueDate: String,
    @SerialName("sale_date") val saleDate: String,
    @SerialName("payment_due_date") val paymentDueDate: String,
    @SerialName("payment_method") val paymentMethod: String,
    @SerialName("bank_account") val bankAccount: String
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
    val invoice: InvoiceMeta, val seller: Participant, val buyer: Participant, val lineItems: List<InvoiceLineInput>
)

@Serializable
data class InvoiceItem(
    val name: String,
    val quantity: Double,
    val unit: String,
    @SerialName("unit_price_net") val unitPriceNet: Double,
    @SerialName("vat_rate") val vatRate: String,
    @SerialName("net_total") val netTotal: Double,
    @SerialName("vat_amount") val vatAmount: Double,
    @SerialName("gross_total") val grossTotal: Double,
)

@Serializable
data class InvoiceOutput(
    val invoice: InvoiceMeta,
    val seller: Participant,
    val buyer: Participant,
    @SerialName("line_items")
    val lineItems: List<InvoiceItem>,
    val totals: InvoiceTotalResult
)


@Tool("format_invoice")
@LLMDescription("Formatuje i zwraca gotowy JSON faktury VAT w restrykcyjnej strukturze.")
fun formatInvoice(
    @LLMDescription("Dane do faktury ")
    data: InvoiceInput
): String {

    val linesCalculated = mutableListOf<InvoiceLineResult>()
    val items = mutableListOf<InvoiceItem>()

    for (item in data.lineItems) {
        val calc = calculateLine(
            quantity = item.quantity, unitPriceNet = item.unitPriceNet, vatRate = item.vatRate
        )

        if (calc.error?.isNotBlank() ?: false) {
            throw IllegalArgumentException("Błąd w pozycji '${item.name}': ${calc.error}")
        }

        linesCalculated.add(
            InvoiceLineResult(
                netTotal = calc.netTotal, vatAmount = calc.vatAmount, grossTotal = calc.grossTotal, error = calc.error
            )
        )

        items.add(
            InvoiceItem(
                name = item.name,
                quantity = item.quantity,
                unit = item.unit,
                vatRate = item.vatRate,
                netTotal = calc.netTotal,
                unitPriceNet = item.unitPriceNet,
                vatAmount = calc.vatAmount,
                grossTotal = calc.grossTotal
            )
        )

    }

    val totals = calculateTotals(linesCalculated.toTypedArray())

    val invoiceOutput =  InvoiceOutput(
        invoice = data.invoice, seller = data.seller, buyer = data.buyer, lineItems = items, totals = totals
    )

    val result = Json.encodeToString(invoiceOutput)
    return result
}