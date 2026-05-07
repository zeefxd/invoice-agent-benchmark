package org.example.domain

import java.nio.file.Path
import java.nio.file.Paths

val ROOT_DIR: Path = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize()
val RESULTS_DIR: Path = ROOT_DIR.resolve("results").resolve("raw")
val SUMMARY_CSV_PATH: Path = ROOT_DIR.resolve("results").resolve("summary.csv")
