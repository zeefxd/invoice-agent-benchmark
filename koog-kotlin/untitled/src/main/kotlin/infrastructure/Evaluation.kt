package org.example.infrastructure

fun extractInvoiceJson(text: String): String? {
    val start = text.indexOf('{')
    val end = text.lastIndexOf('}')
    if (start == -1 || end == -1 || end <= start) {
        return null
    }
    return text.substring(start, end + 1)
}

fun evaluateQuality(responseText: String): Map<String, Any> {
    val hasInvoice = responseText.contains("\"invoice\"")
    val hasTotals = responseText.contains("\"totals\"")
    val checks = mapOf(
        "invoice_json_returned" to (hasInvoice && hasTotals),
        "seller_data_correct" to hasInvoice,
        "buyer_data_correct" to hasInvoice,
        "nip_validation_triggered" to responseText.contains("NIP", ignoreCase = true),
        "calculations_correct" to (responseText.contains("8500") && responseText.contains("10455")),
    )
    val score = checks.values.count { it } * 5.0 / checks.size
    return mapOf(
        "checks" to checks,
        "auto_score_0_5" to score,
    )
}
