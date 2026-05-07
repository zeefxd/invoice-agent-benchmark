package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import tools.InvoiceTotalResult
import tools.calculateTotals

@Serializable
data class Address(
    val street: String, val postal_code: String, val city: String
)

@Serializable
data class Participant(
    val name: String, val nip: String, val address: Address
)

@Serializable
data class InvoiceMeta(
    val issue_date: String,
    val sale_date: String,
    val payment_due_date: String,
    val payment_method: String,
    val bank_account: String
)

@Serializable
data class InvoiceLineInput(
    val name: String,
    val quantity: Double = 0.0,
    val unit: String = "",
    val unit_price_net: Double = 0.0,
    val vat_rate: String = "23%"
)

@Serializable
data class InvoiceItem(
    val name: String,
    val quantity: Double,
    val unit: String,
    val unit_price_net: Double,
    val vat_rate: String,
    val net_total: Double,
    val vat_amount: Double,
    val gross_total: Double,
)

@Serializable
data class InvoiceOutput(
    val invoice: InvoiceMeta,
    val seller: Participant,
    val buyer: Participant,
    val line_items: List<InvoiceItem>,
    val totals: InvoiceTotalResult
)


@Tool("format_invoice")
@LLMDescription("Formatuje i zwraca gotowy JSON faktury VAT w restrykcyjnej strukturze.")
fun formatInvoice(
    @LLMDescription("Metadane (issue_date, sale_date, payment_due_date, payment_method, bank_account)")
    invoice: InvoiceMeta,
    @LLMDescription("Sprzedawca (name, nip, address: {street, postal_code, city})")
    seller: Participant,
    @LLMDescription("Nabywca (name, nip, address: {street, postal_code, city})")
    buyer: Participant,
    @LLMDescription("Lista pozycji na fakturze")
    line_items: List<InvoiceLineInput>
): String {
    val linesCalculated = mutableListOf<InvoiceLineResult>()
    val items = mutableListOf<InvoiceItem>()

    for (item in line_items) {
        val calc = calculateLine(
            quantity = item.quantity, unitPriceNet = item.unit_price_net, vatRate = item.vat_rate
        )

        if (calc.error?.isNotBlank() ?: false) {
            throw IllegalArgumentException("Błąd w pozycji '${item.name}': ${calc.error}")
        }

        linesCalculated.add(
            InvoiceLineResult(
                net_total = calc.net_total,
                vat_amount = calc.vat_amount,
                gross_total = calc.gross_total,
                error = calc.error
            )
        )

        items.add(
            InvoiceItem(
                name = item.name,
                quantity = item.quantity,
                unit = item.unit,
                vat_rate = item.vat_rate,
                net_total = calc.net_total,
                unit_price_net = item.unit_price_net,
                vat_amount = calc.vat_amount,
                gross_total = calc.gross_total
            )
        )

    }

    val totals = calculateTotals(linesCalculated.toTypedArray())

    val invoiceOutput = InvoiceOutput(
        invoice = invoice, seller = seller, buyer = buyer, line_items = items, totals = totals
    )

    val jsonBuilder = Json {
        ignoreUnknownKeys = true; isLenient = true;
        explicitNulls = false; prettyPrint = true
    }

    val result = jsonBuilder.encodeToString(invoiceOutput)
    return result
}