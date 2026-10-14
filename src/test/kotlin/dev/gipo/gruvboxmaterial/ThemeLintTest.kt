package dev.gipo.gruvboxmaterial

import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import org.junit.Assert.fail
import org.junit.Test
import org.w3c.dom.Element
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.math.cbrt
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * Quality gate for every variant in tools/palette.json, under its palette family's rules and restrictions: every color
 * comes from that variant's palette, blue only where the family restricts it to, nothing contrasts more with bg0 than
 * the family's maxContrastColor, no bold/italic where its fontTypes is "none" and exactly groups.json styles where it is
 * "styles", diff tints inside its bounds and changed
 * words apart from their line, no missing or misspelled keys; every runtime foreground level keeps the same bounds
 * against its own fg0. Each test collects every offender across all variants and fails once.
 */
class ThemeLintTest {
    private class Rgba(val rgb: String, val transparent: Boolean)

    private class Variant(val key: String, json: JsonObject) {
        val id: String = json["id"].asString
        val name: String = json["name"].asString
        val dark: Boolean = json["dark"].asBoolean
        val family: String = json["family"].asString
        val parentTheme: String = json["parentTheme"].asString
        val parentScheme: String = json["parentScheme"].asString
        val themePath = "/themes/${json["stem"].asString}.theme.json"
        val schemePath = "/themes/${json["stem"].asString}.xml"
        val colors: Map<String, String> = json.getAsJsonObject("colors").entrySet()
            .associate { it.key to it.value.asString.removePrefix("#").lowercase() }
        val rgb = colors.values.toSet()
        val schemeFamily = "$family-${if (dark) "dark" else "light"}"
        val defaultForeground: String = json["defaultForeground"].asString
        val foregrounds: Map<String, Map<String, String>> = json.getAsJsonObject("foregrounds").entrySet().associate { (level, roles) ->
            level to roles.asJsonObject.entrySet().associate { it.key to it.value.asString.removePrefix("#").lowercase() }
        }
    }

    private val projectDir: File = System.getProperty("projectDir")?.let(::File)
        ?: generateSequence(File(System.getProperty("user.dir")).absoluteFile) { it.parentFile }
            .first { File(it, "tools/palette.json").isFile }

    /** One palette family's entries in tools/palette.json "rules" and "restricted". */
    private class FamilyRules(rules: JsonObject, restricted: JsonObject) {
        val maxContrastColor: String = rules["maxContrastColor"].asString
        val plainFonts = rules["fontTypes"].asString == "none"
        val diff: JsonObject = rules.getAsJsonObject("diff")
        private val blue: JsonObject? = restricted.getAsJsonObject("blue")

        // Null: the family does not restrict blue.
        val blueSchemeKeys = blue?.regexes("schemeKeys")
        val blueThemePaths = blue?.regexes("themePaths")
    }

    private val palette = parseJson(File(projectDir, "tools/palette.json").readText())
    private val variants = palette.getAsJsonObject("variants").entrySet().map { Variant(it.key, it.value.asJsonObject) }
    private val families = palette.getAsJsonObject("rules").entrySet().associate { (family, rules) ->
        family to FamilyRules(rules.asJsonObject, palette.getAsJsonObject("restricted").getAsJsonObject(family) ?: JsonObject())
    }
    private val Variant.rules get() = families[family] ?: throw AssertionError("$key: palette family $family has no rules")

    @Test
    fun descriptorsResolve() {
        val problems = mutableListOf<String>()
        val pluginXml = File(projectDir, "src/main/resources/META-INF/plugin.xml")
        val providers = parseXml(pluginXml.readText()).elements("themeProvider").associate { it.getAttribute("id") to it.getAttribute("path") }
        if (providers.isEmpty()) problems += "plugin.xml: no themeProvider"
        providers.values.filter { resource(it) == null }.forEach { problems += "plugin.xml: themeProvider path $it is not on the classpath" }
        val names = mutableListOf<String>()

        for (v in variants) {
            if (providers[v.id] != v.themePath) problems += "plugin.xml: themeProvider ${v.id} has path ${providers[v.id]}, expected ${v.themePath}"
            val theme = theme(v)
            if (theme == null) {
                problems += "${v.key}: theme ${v.themePath} is not on the classpath"
                continue
            }
            val scheme = theme["editorScheme"]?.asString
            if (scheme == null || resource(scheme) == null) problems += "${v.key}: editorScheme $scheme is not on the classpath"
            if (scheme != v.schemePath) problems += "${v.key}: editorScheme is $scheme, expected ${v.schemePath}"
            theme["name"]?.asString?.let { names += it }
            if (theme["name"]?.asString != v.name) problems += "${v.key}: name is ${theme["name"]}, expected \"${v.name}\""
            if (theme["dark"]?.asBoolean != v.dark) problems += "${v.key}: dark is ${theme["dark"]}, expected ${v.dark}"
            if (theme["parentTheme"]?.asString != v.parentTheme) problems += "${v.key}: parentTheme is ${theme["parentTheme"]}, expected \"${v.parentTheme}\""
        }
        (providers.keys - variants.map { it.id }.toSet()).forEach { problems += "plugin.xml: themeProvider $it has no palette variant" }
        names.groupingBy { it }.eachCount().filterValues { it > 1 }.keys.forEach { problems += "theme name \"$it\" is not unique" }
        report("Descriptor problems", problems)
    }

    @Test
    fun schemeUsesPaletteOnly() = report("Editor scheme colors outside the rules", variants.flatMap { v ->
        val root = scheme(v)
        val problems = mutableListOf<String>()
        val blue = v.colors["blue"]
        val blueSchemeKeys = v.rules.blueSchemeKeys
        if (root.getAttribute("name") != v.name) problems += "scheme name is \"${root.getAttribute("name")}\", expected \"${v.name}\""
        if (root.getAttribute("parent_scheme") != v.parentScheme) problems += "parent_scheme is \"${root.getAttribute("parent_scheme")}\", expected \"${v.parentScheme}\""

        fun checkColor(key: String, where: String, raw: String) {
            if (raw.isEmpty()) return
            val color = parseColor(raw, xml = true)
            when {
                color == null -> problems += "$where: \"$raw\" is not a color"
                color.transparent -> {}
                color.rgb !in v.rgb -> problems += "$where: #${color.rgb} is not in the palette"
                blueSchemeKeys != null && color.rgb == blue && blueSchemeKeys.none { it.containsMatchIn(key) } -> problems += "$where: blue is reserved for ${blueSchemeKeys.map { it.pattern }}"
            }
            if (color != null && !color.transparent && tooContrasty(v, color.rgb)) problems += "$where: #${color.rgb} contrasts more with bg0 than ${v.rules.maxContrastColor}"
        }

        root.child("colors")?.children("option")?.forEach { checkColor(it.getAttribute("name"), "colors.${it.getAttribute("name")}", it.getAttribute("value")) }
        root.child("attributes")?.children("option")?.forEach { attr ->
            val key = attr.getAttribute("name")
            attr.child("value")?.children("option")?.forEach { opt ->
                val name = opt.getAttribute("name")
                val value = opt.getAttribute("value")
                when (name) {
                    in COLOR_OPTIONS -> checkColor(key, "attributes.$key.$name", value)
                    "FONT_TYPE" -> if (v.rules.plainFonts) problems += "attributes.$key: FONT_TYPE $value (no bold/italic, and no explicit 0 either)"
                }
            }
        }
        problems.map { "${v.key}: $it" }
    })

    @Test
    fun schemeDefinesRequiredKeys() = report("Editor scheme keys missing (src/test/resources/scheme-required-keys*.txt)", variants.flatMap { v ->
        val root = scheme(v)
        val defined = mutableSetOf<String>()
        root.child("colors")?.children("option")?.forEach { defined += it.getAttribute("name") }
        root.child("attributes")?.children("option")?.forEach {
            if (it.child("value") != null) defined += it.getAttribute("name")
        }
        keyList(REQUIRED_KEYS[v.schemeFamily] ?: "scheme-required-keys-${v.schemeFamily}.txt").filterNot { it in defined }.map { "${v.key}: $it" }
    })

    @Test
    fun shippedFontTypesAreTheStyleSets() = report("FONT_TYPE keys other than groups.json styles", variants.flatMap { v ->
        val styles = parseJson(resource(GROUPS) ?: throw AssertionError("$GROUPS is not on the classpath"))
            .getAsJsonObject("styles").getAsJsonObject(v.schemeFamily) ?: return@flatMap listOf("${v.key}: no styles for ${v.schemeFamily}")
        val problems = mutableListOf<String>()
        if (styles["shipped"].asBoolean == v.rules.plainFonts) problems += "styles.shipped is ${styles["shipped"]}, fontTypes says otherwise"
        if (!v.rules.plainFonts) {
            val bold = styles.getAsJsonArray("bold").map { it.asString }.toSet()
            val italic = styles.getAsJsonArray("italic").map { it.asString }.toSet()
            val expected = (bold + italic).associateWith { (if (it in bold) 1 else 0) + (if (it in italic) 2 else 0) }
            val shipped = scheme(v).child("attributes")?.children("option").orEmpty().mapNotNull { attr ->
                attr.child("value")?.children("option")?.firstOrNull { it.getAttribute("name") == "FONT_TYPE" }
                    ?.let { attr.getAttribute("name") to it.getAttribute("value").toInt() }
            }.toMap()
            (expected.keys + shipped.keys).filter { expected[it] != shipped[it] }.sorted()
                .forEach { problems += "$it: FONT_TYPE ${shipped[it]}, styles ${expected[it]}" }
        }
        problems.map { "${v.key}: $it" }
    })

    // IntelliJ does not follow baseAttributes to the named key: it uses the key's coded fallback, else Darcula's value.
    @Test
    fun schemeHasNoBaseAttributes() = report("Editor scheme links (write an explicit <value>)", variants.flatMap { v ->
        scheme(v).child("attributes")?.children("option").orEmpty()
            .filter { it.hasAttribute("baseAttributes") }
            .map { "${v.key}: attributes.${it.getAttribute("name")}: baseAttributes=\"${it.getAttribute("baseAttributes")}\"" }
    })

    // The section-2 diff bounds in tools/palette.json, on the tints each scheme actually writes. TextDiffType paints
    // BACKGROUND for blocks and changed words, FOREGROUND for the line under word highlights.
    @Test
    fun diffTintsMeetBounds() {
        report("Diff tints outside the bounds", variants.flatMap { v ->
            val diff = v.rules.diff
            val problems = mutableListOf<String>()
            val bg = v.colors.getValue("bg0")
            val fg = v.colors.getValue("fg0")
            val attrs = scheme(v).child("attributes")?.children("option").orEmpty().associateBy { it.getAttribute("name") }
            val byKind = mutableMapOf<String, Map<String, String>>()
            for ((kind, field) in DIFF_FIELDS) {
                val spec = diff.getAsJsonObject(kind)
                val (low, high) = spec.getAsJsonArray("deltaE").map { it.asDouble }
                // fg0 on the tint keeps this share of its contrast on bg0, for every foreground level's fg0.
                val ratio = spec["contrastRatio"].asDouble
                val floor = ratio * contrast(fg, bg)
                val tintsByKey = DIFF_KEYS.mapNotNull { key ->
                    val raw = attrs[key]?.child("value")?.children("option")?.firstOrNull { it.getAttribute("name") == field }?.getAttribute("value")
                    if (raw.isNullOrEmpty()) {
                        problems += "$key.$field is not set"
                        return@mapNotNull null
                    }
                    val tint = parseColor(raw, xml = true)!!.rgb
                    val distance = deltaE(tint, bg)
                    if (distance < low || distance > high) problems += "$key.$field #$tint: deltaE ${"%.3f".format(distance)} vs bg0 outside [$low, $high]"
                    if (contrast(fg, tint) < floor) problems += "$key.$field #$tint: fg0 contrast ${"%.2f".format(contrast(fg, tint))} < ${"%.2f".format(floor)}"
                    for ((level, roles) in v.foregrounds) {
                        val levelFg = roles.getValue("fg0")
                        val levelFloor = ratio * contrast(levelFg, bg)
                        if (contrast(levelFg, tint) < levelFloor) problems += "$key.$field #$tint: $level fg0 contrast ${"%.2f".format(contrast(levelFg, tint))} < ${"%.2f".format(levelFloor)}"
                    }
                    key to tint
                }.toMap()
                byKind[kind] = tintsByKey
                val tints = tintsByKey.values.toList()
                val pairwise = spec["pairwise"].asDouble
                for (i in tints.indices) for (j in i + 1 until tints.size) {
                    if (deltaE(tints[i], tints[j]) < pairwise) problems += "$kind #${tints[i]} vs #${tints[j]}: deltaE ${"%.3f".format(deltaE(tints[i], tints[j]))} < $pairwise"
                }
                val lightness = tints.map { oklab(it)[0] }
                if (kind == "block" && lightness.isNotEmpty() && lightness.max() - lightness.min() > 0.01) problems += "block tints differ in lightness by ${"%.3f".format(lightness.max() - lightness.min())}"
            }
            // Changed words (block tint) must stand out from their changed line (line tint).
            val wordVsLine = diff["wordVsLine"].asDouble
            for (key in DIFF_KEYS) {
                val word = byKind.getValue("block")[key] ?: continue
                val line = byKind.getValue("line")[key] ?: continue
                if (deltaE(word, line) < wordVsLine) problems += "$key word #$word vs line #$line: deltaE ${"%.3f".format(deltaE(word, line))} < $wordVsLine"
            }
            problems.map { "${v.key}: $it" }
        })
    }

    @Test
    fun themeUsesPaletteOnly() = report("Theme colors outside the rules", variants.flatMap { v ->
        val theme = theme(v) ?: throw AssertionError("theme ${v.themePath} is not on the classpath")
        val blue = v.colors["blue"]
        val blueThemePaths = v.rules.blueThemePaths
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
                    color.rgb !in v.rgb -> problems += "$path: \"$raw\" (#${color.rgb}) is not in the palette"
                    blueThemePaths != null && color.rgb == blue && blueThemePaths.none { it.containsMatchIn(path) } -> problems += "$path: blue is reserved for ${blueThemePaths.map { it.pattern }}"
                    tooContrasty(v, color.rgb) -> problems += "$path: #${color.rgb} contrasts more with bg0 than ${v.rules.maxContrastColor}"
                }
            }
        }
        problems.map { "${v.key}: $it" }
    })

    // The runtime keyword choices may be dim (faint and ghost rows sit below 4.5:1 on purpose), never brighter than text.
    @Test
    fun keywordChoicesStayBelowText() {
        val runtime = parseJson(resource(RUNTIME_PALETTE) ?: throw AssertionError("$RUNTIME_PALETTE is not on the classpath"))
            .getAsJsonObject("variants")
        report("Keyword choices contrasting more with bg0 than their family's maxContrastColor", variants.flatMap { v ->
            val families = runtime.getAsJsonObject(v.id)?.getAsJsonObject("keywords")?.getAsJsonObject("families")
                ?: return@flatMap listOf("${v.key}: no keywords in $RUNTIME_PALETTE")
            families.entrySet().flatMap { (family, node) ->
                node.asJsonObject.getAsJsonArray("colors").flatMapIndexed { row, cells ->
                    cells.asJsonArray.map { it.asString.removePrefix("#").lowercase() }
                        .filter { tooContrasty(v, it) }.map { "${v.key}: $family row $row #$it" }
                }
            }
        })
    }

    // The runtime text contrast switch swaps every foreground role for its level's value: each level must stay in its
    // palette and below its own fg0, ship the same roles at runtime, and the shipped level must be the shipped roles.
    // The runtime variant names its family and lists every level once, in order, with a label.
    @Test
    fun foregroundLevelsStayInBounds() {
        val runtime = parseJson(resource(RUNTIME_PALETTE) ?: throw AssertionError("$RUNTIME_PALETTE is not on the classpath"))
            .getAsJsonObject("variants")
        report("Foreground levels outside the rules", variants.flatMap { v ->
            val problems = mutableListOf<String>()
            val shipped = v.foregrounds[v.defaultForeground]
            if (shipped == null) return@flatMap listOf("${v.key}: no default foreground level ${v.defaultForeground}")
            shipped.filter { (role, hex) -> v.colors[role] != hex }.forEach { (role, hex) -> problems += "${v.defaultForeground}.$role #$hex is not the shipped #${v.colors[role]}" }
            // Icon palettes are applied when the theme loads: no level recolours them, so the main cap check covers them.
            val used = usedColors(v, listOf("colors", "ui"))
            val runtimeVariant = runtime.getAsJsonObject(v.id)
            val runtimeLevels = runtimeVariant?.getAsJsonObject("foregrounds")
            if (runtimeVariant?.get("family")?.asString != v.family) problems += "$RUNTIME_PALETTE family is ${runtimeVariant?.get("family")}, expected ${v.family}"
            val labelled = runtimeVariant?.getAsJsonArray("foregroundLevels")?.map { it.asJsonObject }.orEmpty()
            val ids = labelled.map { it["id"]?.asString }
            if (ids != v.foregrounds.keys.toList()) problems += "foregroundLevels $ids differ from the levels ${v.foregrounds.keys}"
            labelled.filter { it["label"]?.asString.isNullOrBlank() }.forEach { problems += "foregroundLevels ${it["id"]}: no label" }
            for ((level, roles) in v.foregrounds) {
                if (roles.keys != shipped.keys) problems += "$level: roles ${roles.keys.sorted()} differ from ${shipped.keys.sorted()}"
                val fg = roles.getValue("fg0")
                val swap = shipped.entries.associate { (role, hex) -> hex to roles.getValue(role) }
                for (rgb in used) {
                    val color = swap[rgb] ?: rgb
                    if (tooContrasty(v, color, fg)) problems += "$level: #$color (shipped #$rgb) contrasts more with bg0 than its fg0 #$fg"
                }
                val node = runtimeLevels?.getAsJsonObject(level)
                if (node == null) {
                    problems += "$level: missing in $RUNTIME_PALETTE"
                    continue
                }
                val runtimeRoles = node.getAsJsonObject("roles").entrySet().associate { it.key to it.value.asString.removePrefix("#").lowercase() }
                if (runtimeRoles != roles) problems += "$level: $RUNTIME_PALETTE roles differ from tools/palette.json"
                node.getAsJsonObject("keywords").getAsJsonObject("families").entrySet().forEach { (family, f) ->
                    f.asJsonObject.getAsJsonArray("colors").forEachIndexed { row, cells ->
                        cells.asJsonArray.map { it.asString.removePrefix("#").lowercase() }
                            .filter { tooContrasty(v, it, fg) }.forEach { problems += "$level: keyword $family row $row #$it contrasts more with bg0 than its fg0" }
                    }
                }
            }
            problems.map { "${v.key}: $it" }
        })
    }

    // Every opaque rgb the variant's scheme and theme write, theme color names resolved.
    private fun usedColors(v: Variant, sections: List<String>): Set<String> {
        val out = mutableSetOf<String>()
        fun add(color: Rgba?) {
            if (color != null && !color.transparent) out += color.rgb
        }
        val root = scheme(v)
        root.child("colors")?.children("option")?.forEach { add(parseColor(it.getAttribute("value"), xml = true)) }
        root.child("attributes")?.children("option")?.forEach { attr ->
            attr.child("value")?.children("option")?.filter { it.getAttribute("name") in COLOR_OPTIONS }
                ?.forEach { add(parseColor(it.getAttribute("value"), xml = true)) }
        }
        val theme = theme(v) ?: throw AssertionError("theme ${v.themePath} is not on the classpath")
        val named = theme.getAsJsonObject("colors")?.entrySet()?.filter { it.value.isJsonPrimitive }?.associate { it.key to it.value.asString }.orEmpty()
        for (section in sections) {
            val node = theme[section] ?: continue
            leaves(node, section).forEach { (_, raw) ->
                var value = raw
                repeat(named.size + 1) { named[value]?.let { value = it } }
                add(parseColor(value, xml = false))
            }
        }
        return out
    }

    @Test
    fun uiKeysAreKnown() {
        val known = keyList("known-ui-keys.txt").toSet()
        report("Unknown ui keys (typo, or regenerate src/test/resources/known-ui-keys.txt)", variants.flatMap { v ->
            val theme = theme(v) ?: throw AssertionError("theme ${v.themePath} is not on the classpath")
            theme.getAsJsonObject("ui")?.let { leaves(it, null, keepNonStrings = true) }.orEmpty()
                .map { it.first }.filterNot { it in known }.map { "${v.key}: $it" }
        })
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

    private fun contrast(a: String, b: String): Double {
        val (hi, lo) = listOf(luminance(a), luminance(b)).sortedDescending()
        return (hi + 0.05) / (lo + 0.05)
    }

    private fun tooContrasty(v: Variant, rgb: String, fg: String = v.colors.getValue(v.rules.maxContrastColor)): Boolean {
        val bg = v.colors.getValue("bg0")
        return contrast(rgb, bg) > contrast(fg, bg) + 1e-9
    }

    // OKLab (Ottosson), sRGB linearised with the 0.04045 threshold.
    private fun oklab(rgb: String): DoubleArray {
        fun lin(i: Int): Double {
            val c = rgb.substring(i, i + 2).toInt(16) / 255.0
            return if (c <= 0.04045) c / 12.92 else ((c + 0.055) / 1.055).pow(2.4)
        }
        val (r, g, b) = listOf(lin(0), lin(2), lin(4))
        val l = cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
        val m = cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
        val s = cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
        return doubleArrayOf(
            0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
        )
    }

    private fun deltaE(a: String, b: String): Double {
        val (x, y) = oklab(a) to oklab(b)
        return sqrt((0..2).sumOf { (x[it] - y[it]).pow(2) })
    }

    private fun theme(v: Variant): JsonObject? = resource(v.themePath)?.let { parseJson(it) }

    private fun scheme(v: Variant): Element {
        val path = theme(v)?.get("editorScheme")?.asString ?: v.schemePath
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

    private fun Element.children(tag: String): List<Element> =
        (0 until childNodes.length).map { childNodes.item(it) }.filterIsInstance<Element>().filter { it.tagName == tag }

    private fun Element.child(tag: String): Element? = children(tag).firstOrNull()

    private fun Element.elements(tag: String): List<Element> =
        getElementsByTagName(tag).let { list -> (0 until list.length).map { list.item(it) as Element } }

    companion object {
        const val RUNTIME_PALETTE = "/gruvbox/palette.json"
        const val GROUPS = "/gruvbox/groups.json"
        // Material's lists predate per-family names; other scheme families use scheme-required-keys-<family>.txt.
        val REQUIRED_KEYS = mapOf("material-dark" to "scheme-required-keys.txt", "material-light" to "scheme-required-keys-light.txt")
        val DIFF_KEYS = listOf("DIFF_INSERTED", "DIFF_DELETED", "DIFF_MODIFIED", "DIFF_CONFLICT")
        val DIFF_FIELDS = mapOf("block" to "BACKGROUND", "line" to "FOREGROUND")
        val COLOR_OPTIONS = setOf("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")
        val HEX_LIKE = Regex("^[0-9a-f]{3,8}$")
        val COLOR_FUNCTION = Regex("^(rgba?|hsla?|hsb)\\s*\\(")
        val COLOR_WORDS = setOf(
            "black", "white", "gray", "grey", "darkgray", "darkgrey", "lightgray", "lightgrey", "red", "green", "blue",
            "yellow", "orange", "pink", "magenta", "cyan", "purple", "brown", "transparent",
        )

        fun parseJson(text: String): JsonObject = JsonParser.parseString(text).asJsonObject

        private fun JsonObject.regexes(key: String) = getAsJsonArray(key).map { Regex(it.asString) }

        fun parseXml(text: String): Element =
            DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(text.byteInputStream()).documentElement
    }
}
