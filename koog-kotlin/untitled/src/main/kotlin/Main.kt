package org.example

import org.example.interfaces.CliRunner

suspend fun main() {
    val debug = java.lang.Boolean.getBoolean("debug")
    CliRunner.executeAll(debug)
}
