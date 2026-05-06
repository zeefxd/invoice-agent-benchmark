plugins {
    kotlin("jvm") version "2.3.20"
    kotlin("plugin.serialization") version "2.3.20"
    application
    id("com.gradleup.shadow") version "9.4.1"
}

group = "org.example"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

val ktorVer = "3.4.3"
val koogVer = "0.8.0"

dependencies {
    testImplementation(kotlin("test"))
    implementation("ai.koog:koog-ktor:$koogVer")
    implementation("ai.koog:koog-agents:$koogVer")
    implementation("io.ktor:ktor-client-core:$ktorVer")
    implementation("io.ktor:ktor-client-cio:$ktorVer")
    implementation("io.ktor:ktor-client-content-negotiation:$ktorVer")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.11.0")
}


application {
    mainClass.set("org.example.MainKt")
}

kotlin {
    jvmToolchain(21)
}

tasks.test {
    useJUnitPlatform()
}

tasks.named<JavaExec>("run") {
    standardInput = System.`in`
}

tasks.jar {
    manifest {
        attributes["Main-Class"] = "org.example.MainKt"
    }
}