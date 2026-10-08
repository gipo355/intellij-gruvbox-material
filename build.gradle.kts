plugins {
    id("org.jetbrains.kotlin.jvm") version "2.3.21"
    id("org.jetbrains.intellij.platform") version "2.18.1"
}

group = "dev.gipo.gruvboxmaterial"
version = "0.1.0" // x-release-please-version

repositories {
    mavenCentral()
    intellijPlatform { defaultRepositories() }
}

// Local IDE from ideaHome in ~/.gradle/gradle.properties when it exists (dev machine), otherwise a
// downloaded IU so CI can build. Override with -PplatformVersion=2026.2.1.
val ideaHome = providers.gradleProperty("ideaHome").map { file(it) }
val hasLocalIde = ideaHome.map { it.isDirectory }.getOrElse(false)
val platformVersion = providers.gradleProperty("platformVersion").getOrElse("2026.2")

dependencies {
    intellijPlatform {
        if (hasLocalIde) local(providers.gradleProperty("ideaHome")) else intellijIdeaUltimate(platformVersion)
        bundledPlugins("com.intellij.java", "org.jetbrains.kotlin", "JavaScript")
    }
    testImplementation(kotlin("stdlib"))
    testImplementation("junit:junit:4.13.2")
    testImplementation("com.google.code.gson:gson:2.13.2")
}

kotlin {
    jvmToolchain(25)
}

intellijPlatform {
    pluginConfiguration {
        // CI passes the GitHub release notes; local builds ship without change notes.
        changeNotes = providers.environmentVariable("CHANGE_NOTES")
        ideaVersion {
            sinceBuild = "262"
            untilBuild = provider { null }
        }
    }
    buildSearchableOptions = false
    pluginVerification {
        ides { if (hasLocalIde) local(ideaHome) else recommended() }
    }
}

tasks.test {
    // The lint reads the palette from tools/, outside every source set: rerun when it changes.
    inputs.file("tools/palette.json")
    systemProperty("projectDir", projectDir.absolutePath)
    // Print the offender lists, not just "AssertionError at ThemeLintTest.kt".
    testLogging { exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL }
}
