package org.example.tools

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import kotlinx.serialization.Serializable

@Serializable
data class NipValidationResult(
    val valid: Boolean,
    val message: String
)

@Tool("validate_nip")
@LLMDescription("Sprawdza poprawność numeru NIP (polska suma kontrolna)")
fun validateNIP(
    @LLMDescription("Numer NIP jako string (może zawierać myślniki/spacje)")
    nip: String
): NipValidationResult {

    val digits = nip.replace(Regex("\\D"), "")

    if (digits.length != 10) {
        return NipValidationResult(
            valid = false,
            message = "NIP musi mieć 10 cyfr, podano ${digits.length}."
        )
    }

    val weights = listOf(6, 5, 7, 2, 3, 4, 5, 6, 7)

    val checksum = weights.indices.sumOf {
        digits[it].digitToInt() * weights[it]
    } % 11

    val result = if (checksum == digits[9].digitToInt()) {
        NipValidationResult(true, "NIP jest poprawny.")
    } else {
        NipValidationResult(false, "NIP ma błędną sumę kontrolną.")
    }

    println("validate_nip: $result")
    return result
}