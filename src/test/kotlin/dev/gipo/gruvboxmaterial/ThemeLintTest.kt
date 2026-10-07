package dev.gipo.gruvboxmaterial

import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import org.junit.Assert.fail
import org.junit.Test
import org.w3c.dom.Element
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.math.pow

/**
 * Quality gate for the theme: every color comes from tools/palette.json, blue only where
 * restricted allows it, nothing brighter than fg0, no bold/italic, no missing or misspelled keys.
 * Each test collects every offender and fails once.
 */
class ThemeLintTest {
    private class Rgba(val rgb: String, val transparent: Boolean)

    private val projectDir: File = System.getProperty("projectDir")?.let(::File)
        ?: generateSequence(File(System.getProperty("user.dir")).absoluteFile) { it.parentFile }
            .first { File(it, "tools/palette.json").isFile }

    private val palette = parseJson(File(projectDir, "tools/palette.json").readText())
    private val paletteColors: Map<String, String> = palette.getAsJsonObject("colors").entrySet()
        .filterNot { it.key.startsWith("$") }
        .associate { it.key to it.value.asString.removePrefix("#").lowercase() }
    private val paletteRgb = paletteColors.values.toSet()
    private val blue = paletteColors.getValue("blue")
    private val maxLuminance = luminance(paletteColors.getValue(palette.getAsJsonObject("rules")["maxLuminanceColor"].asString))
    private val blueRules = palette.getAsJsonObject("restricted").getAsJsonObject("blue")
    private val blueSchemeKeys = blueRules.regexes("schemeKeys")
    private val blueThemePaths = blueRules.regexes("themePaths")

    @Test
    fun descriptorsResolve() {
        val problems = mutableListOf<String>()
        val pluginXml = File(projectDir, "src/main/resources/META-INF/plugin.xml")
        val themePaths = parseXml(pluginXml.readText()).elements("themeProvider").map { it.getAttribute("path") }
        if (themePaths.isEmpty()) problems += "plugin.xml: no themeProvider"
        themePaths.filter { resource(it) == null }.forEach { problems += "plugin.xml: themeProvider path $it is not on the classpath" }

        val theme = theme()
        if (theme == null) {
            problems += "theme $THEME_PATH is not on the classpath"
        } else {
            val scheme = theme["editorScheme"]?.asString
            if (scheme == null || resource(scheme) == null) problems += "theme.json: editorScheme $scheme is not on the classpath"
            if (theme["name"]?.asString != NAME) problems += "theme.json: name is ${theme["name"]}, expected \"$NAME\""
            if (theme["dark"]?.asBoolean != true) problems += "theme.json: dark is ${theme["dark"]}, expected true"
            if (theme["parentTheme"]?.asString != "ExperimentalDark") problems += "theme.json: parentTheme is ${theme["parentTheme"]}, expected \"ExperimentalDark\""
        }
        report("Descriptor problems", problems)
    }

    @Test
    fun schemeUsesPaletteOnly() {
        val root = scheme()
        val problems = mutableListOf<String>()
        if (root.getAttribute("name") != NAME) problems += "scheme name is \"${root.getAttribute("name")}\", expected \"$NAME\""
        if (root.getAttribute("parent_scheme") != "Darcula") problems += "parent_scheme is \"${root.getAttribute("parent_scheme")}\", expected \"Darcula\""

        fun checkColor(key: String, where: String, raw: String) {
            if (raw.isEmpty()) return
            val color = parseColor(raw, xml = true)
            when {
                color == null -> problems += "$where: \"$raw\" is not a color"
                color.transparent -> {}
                color.rgb !in paletteRgb -> problems += "$where: #${color.rgb} is not in the palette"
                color.rgb == blue && blueSchemeKeys.none { it.containsMatchIn(key) } -> problems += "$where: blue is reserved for ${blueSchemeKeys.map { it.pattern }}"
            }
            if (color != null && !color.transparent && luminance(color.rgb) > maxLuminance) problems += "$where: #${color.rgb} is brighter than fg0"
        }

        root.child("colors")?.children("option")?.forEach { checkColor(it.getAttribute("name"), "colors.${it.getAttribute("name")}", it.getAttribute("value")) }
        root.child("attributes")?.children("option")?.forEach { attr ->
            val key = attr.getAttribute("name")
            attr.child("value")?.children("option")?.forEach { opt ->
                val name = opt.getAttribute("name")
                val value = opt.getAttribute("value")
                when (name) {
                    in COLOR_OPTIONS -> checkColor(key, "attributes.$key.$name", value)
                    "FONT_TYPE" -> if (value.isNotEmpty() && value != "0") problems += "attributes.$key: FONT_TYPE $value (no bold/italic)"
                }
            }
        }
        report("Editor scheme colors outside the rules", problems)
    }

    @Test
    fun schemeDefinesRequiredKeys() {
        val root = scheme()
        val defined = mutableSetOf<String>()
        root.child("colors")?.children("option")?.forEach { defined += it.getAttribute("name") }
        root.child("attributes")?.children("option")?.forEach {
            if (it.child("value") != null) defined += it.getAttribute("name")
        }
        val missing = keyList("scheme-required-keys.txt").filterNot { it in defined }
        report("Editor scheme keys missing (src/test/resources/scheme-required-keys.txt)", missing)
    }

    // IntelliJ does not follow baseAttributes to the named key: it uses the key's coded fallback, else Darcula's value.
    @Test
    fun schemeHasNoBaseAttributes() {
        val linked = scheme().child("attributes")?.children("option").orEmpty()
            .filter { it.hasAttribute("baseAttributes") }
            .map { "attributes.${it.getAttribute("name")}: baseAttributes=\"${it.getAttribute("baseAttributes")}\"" }
        report("Editor scheme links (write an explicit <value>)", linked)
    }

    @Test
    fun themeUsesPaletteOnly() {
        val theme = theme() ?: throw AssertionError("theme $THEME_PATH is not on the classpath")
        val named: Map<String, String> = theme.getAsJsonObject("colors")?.entrySet()
            ?.filter { it.value.isJsonPrimitive }?.associate { it.key to it.value.asString }.orEmpty()
        val problems = mutableListOf<String>()

        fun resolve(raw: String, seen: List<String> = emptyList()): Rgba? {
            parseColor(raw, xml = false)?.let { return it }
            val next = named[raw] ?: return null
            if (raw in seen) throw IllegalStateException("color name cycle: ${(seen + raw).joinToString(" -> ")}")
            return resolve(next, seen + raw)
        }

        for (section in listOf("colors", "ui", "icons", "iconColorsOnSelection")) {
            val node = theme[section] ?: continue
            leaves(node, section).forEach { (path, raw) ->
                val color = try {
                    resolve(raw)
                } catch (e: IllegalStateException) {
                    problems += "$path: ${e.message}"
                    return@forEach
                }
                when {
                    color == null -> if (section == "colors" || looksLikeColor(raw)) problems += "$path: \"$raw\" is neither a color nor a color name"
                    color.transparent -> {}
                    color.rgb !in paletteRgb -> problems += "$path: \"$raw\" (#${color.rgb}) is not in the palette"
                    color.rgb == blue && blueThemePaths.none { it.containsMatchIn(path) } -> problems += "$path: blue is reserved for ${blueThemePaths.map { it.pattern }}"
                }
            }
        }
        report("Theme colors outside the rules", problems)
    }

    @Test
    fun uiKeysAreKnown() {
        val theme = theme() ?: throw AssertionError("theme $THEME_PATH is not on the classpath")
        val known = keyList("known-ui-keys.txt").toSet()
        val unknown = theme.getAsJsonObject("ui")?.let { leaves(it, null, keepNonStrings = true) }.orEmpty()
            .map { it.first }.filterNot { it in known }
        report("Unknown ui keys (typo, or regenerate src/test/resources/known-ui-keys.txt)", unknown)
    }

    // Flattened (path, string value) leaves, keys joined with "."; `$` keys are comments.
    private fun leaves(node: JsonElement, prefix: String?, keepNonStrings: Boolean = false): List<Pair<String, String>> = when {
        node.isJsonObject -> node.asJsonObject.entrySet().filterNot { it.key.startsWith("$") }
            .flatMap { leaves(it.value, if (prefix == null) it.key else "$prefix.${it.key}", keepNonStrings) }
        node.isJsonPrimitive && node.asJsonPrimitive.isString -> listOf(prefix!! to node.asString)
        keepNonStrings -> listOf(prefix!! to node.toString())
        else -> emptyList()
    }

    // Values a theme reader would take as a color but parseColor rejects: #rgb, bare hex, rgb()/hsl(), AWT/CSS names.
    private fun looksLikeColor(raw: String): Boolean {
        val v = raw.trim().lowercase()
        return v.startsWith("#") || HEX_LIKE.matches(v) || COLOR_FUNCTION.containsMatchIn(v) || v in COLOR_WORDS
    }

    private fun parseColor(raw: String, xml: Boolean): Rgba? {
        var hex = raw.trim()
        val hashed = hex.startsWith("#")
        hex = hex.removePrefix("#").lowercase()
        if (hex.isEmpty() || !hex.all { it in '0'..'9' || it in 'a'..'f' }) return null
        // IntelliJ writes scheme colors without leading zeros ("76678" = #076678).
        if (xml && hex.length < 6) hex = hex.padStart(6, '0')
        return when {
            hex.length == 6 -> Rgba(hex, false)
            hex.length == 8 && (hashed || xml) -> Rgba(hex.substring(0, 6), hex.substring(6) == "00")
            else -> null
        }
    }

    private fun luminance(rgb: String): Double {
        fun channel(i: Int): Double {
            val c = rgb.substring(i, i + 2).toInt(16) / 255.0
            return if (c <= 0.03928) c / 12.92 else ((c + 0.055) / 1.055).pow(2.4)
        }
        return 0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4)
    }

    private fun theme(): JsonObject? = resource(THEME_PATH)?.let { parseJson(it) }

    private fun scheme(): Element {
        val path = theme()?.get("editorScheme")?.asString ?: SCHEME_PATH
        val text = resource(path) ?: throw AssertionError("editor scheme $path is not on the classpath")
        return parseXml(text)
    }

    private fun keyList(name: String): List<String> {
        val text = resource(name) ?: throw AssertionError("src/test/resources/$name is missing")
        return text.lines().map { it.trim() }.filter { it.isNotEmpty() && !it.startsWith("#") }
    }

    private fun resource(path: String): String? = javaClass.getResource("/" + path.removePrefix("/"))?.readText()

    private fun report(title: String, problems: List<String>) {
        if (problems.isNotEmpty()) fail("$title (${problems.size}):\n" + problems.joinToString("\n") { "  $it" })
    }

    private fun JsonObject.regexes(key: String) = getAsJsonArray(key).map { Regex(it.asString) }

    private fun Element.children(tag: String): List<Element> =
        (0 until childNodes.length).map { childNodes.item(it) }.filterIsInstance<Element>().filter { it.tagName == tag }

    private fun Element.child(tag: String): Element? = children(tag).firstOrNull()

    private fun Element.elements(tag: String): List<Element> =
        getElementsByTagName(tag).let { list -> (0 until list.length).map { list.item(it) as Element } }

    companion object {
        const val NAME = "Gruvbox Material Islands"
        const val THEME_PATH = "/themes/GruvboxMaterialIslands.theme.json"
        const val SCHEME_PATH = "/themes/GruvboxMaterialIslands.xml"
        val COLOR_OPTIONS = setOf("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")
        val HEX_LIKE = Regex("^[0-9a-f]{3,8}$")
        val COLOR_FUNCTION = Regex("^(rgba?|hsla?|hsb)\\s*\\(")
        val COLOR_WORDS = setOf(
            "black", "white", "gray", "grey", "darkgray", "darkgrey", "lightgray", "lightgrey", "red", "green", "blue",
            "yellow", "orange", "pink", "magenta", "cyan", "purple", "brown", "transparent",
        )

        fun parseJson(text: String): JsonObject = JsonParser.parseString(text).asJsonObject

        fun parseXml(text: String): Element =
            DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(text.byteInputStream()).documentElement
    }
}
