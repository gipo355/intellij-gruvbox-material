package dev.gipo.gruvboxmaterial.settings

import com.google.gson.JsonObject
import com.google.gson.JsonParser
import java.awt.Color

data class Variant(
    val id: String,
    val name: String,
    val dark: Boolean,
    val editorScheme: String,
    val roles: Map<String, Color>,
    val keywords: KeywordTable? = null,
    val defaultForeground: String? = null,
    val foregrounds: Map<String, Foreground> = emptyMap(),
    /** The palette family, e.g. material: text contrast choices are kept per palette family. */
    val paletteFamily: String = "material",
    /** The text contrast levels in menu order. */
    val levels: List<Level> = emptyList(),
) {
    /** The key of the per-family tables in groups.json: palette family and parent axis, e.g. material-dark. */
    val schemeFamily get() = "$paletteFamily-${if (dark) "dark" else "light"}"

    /** [id] when it names one of this variant's levels, else null (the default). */
    fun level(id: String?): String? = id?.takeIf { foregrounds.containsKey(it) }

    /** This variant at text contrast [level]: its roles overlaid with the level's and the level's keyword table; null is the default. */
    fun atLevel(level: String?): Variant {
        val foreground = foregrounds[level ?: defaultForeground] ?: return this
        return copy(roles = roles + foreground.roles, keywords = foreground.keywords ?: keywords)
    }
}

/** One text contrast level, upstream gruvbox-material's foreground option. */
data class Foreground(val roles: Map<String, Color>, val keywords: KeywordTable?)

/** A text contrast level as the settings list it. */
data class Level(val id: String, val label: String)

/** What [variant]'s text contrast levels follow, for the settings comment. */
fun textContrastComment(variant: Variant?): String = when (variant?.paletteFamily) {
    "baby" -> "Baby is gruvbox-baby as it ships, Original its use_original_palette, Tuned its hues at gruvbox-material's contrast"
    else -> "Follows upstream gruvbox-material's foreground option"
}

/** What Bold and Italic cover in [variant]'s palette family, for the settings comments. */
fun styleComments(variant: Variant?): Pair<String, String> = when (variant?.paletteFamily) {
    "baby" -> "Functions, methods, constants and annotations, as gruvbox-baby ships them" to
        "Keywords and comments, as gruvbox-baby ships them"
    else -> "Functions, methods, calls and macros, like upstream enable_bold" to
        "Types, namespaces and builtins, like upstream enable_italic; comments stay on Italic comments"
}

/** [level]'s label, or for null the default entry naming [variant]'s default level. */
fun textContrastLabel(variant: Variant?, level: Level?): String =
    level?.label ?: variant?.levels?.firstOrNull { it.id == variant.defaultForeground }?.let { "Default (${it.label})" } ?: "Default"

/** Keyword colours per family as rows of brightness, each row `[vivid, muted, soft]`. */
data class KeywordTable(
    val brightness: List<String>,
    val strength: List<String>,
    val families: Map<String, KeywordFamily>,
)

data class KeywordFamily(val label: String, val colors: List<List<Color>>)

data class Groups(
    val operators: List<String>,
    val comments: List<String>,
    val docs: List<String>,
    val calls: List<String>,
    val accentUiKeys: Map<String, List<String>> = emptyMap(),
    val keywords: List<String> = emptyList(),
    val parameters: List<String> = emptyList(),
    val reassigned: List<String> = emptyList(),
    val annotations: List<String> = emptyList(),
    val schemeForegroundRoles: Map<String, SchemeRoles> = emptyMap(),
    val uiForegroundKeys: Map<String, Map<String, List<String>>> = emptyMap(),
    val highUiContrast: Map<String, Map<String, RoleStep>> = emptyMap(),
    /** Per scheme family, the key groups above as that family's scheme links them. */
    val keyGroups: Map<String, Map<String, List<String>>> = emptyMap(),
    val styles: Map<String, Styles> = emptyMap(),
    /** Per scheme family, the role its shipped accent ui keys use. */
    val accentRole: Map<String, String> = emptyMap(),
) {
    /** These groups with the key lists of [schemeFamily]'s own scheme, when groups.json has them. */
    fun forFamily(schemeFamily: String): Groups {
        val k = keyGroups[schemeFamily] ?: return this
        fun list(name: String) = k[name].orEmpty()
        return copy(
            operators = list("operators"), comments = list("comments"), docs = list("docs"), calls = list("calls"), keywords = list("keywords"),
            parameters = list("parameters"), reassigned = list("reassigned"), annotations = list("annotations"),
        )
    }

    fun shipsStyles(variant: Variant): Boolean = styles[variant.schemeFamily]?.shipped ?: false
}

/** The keys a palette family draws bold or italic, and whether its scheme ships them that way. */
data class Styles(val bold: List<String>, val italic: List<String>, val shipped: Boolean)

/** A key's shipped role and the one high UI contrast raises it to. */
data class RoleStep(val from: String, val to: String)

/** The scheme keys whose colour is a foreground role, per scheme family: colour keys, and attribute fields such as FOREGROUND. */
data class SchemeRoles(val colors: Map<String, String>, val attributes: Map<String, Map<String, String>>)

/** The generated palette.json and groups.json: variants keyed by themeProvider id, and the key groups the toggles recolor. */
class Palette(val variants: Map<String, Variant>, val groups: Groups) {
    fun variantForScheme(schemeName: String): Variant? = variants.values.firstOrNull { it.editorScheme == schemeName }

    companion object {
        fun parse(paletteJson: String, groupsJson: String): Palette {
            val variants = JsonParser.parseString(paletteJson).asJsonObject.getAsJsonObject("variants").entrySet().associate { (id, v) ->
                val o = v.asJsonObject
                id to Variant(
                    id = id,
                    name = o["name"].asString,
                    dark = o["dark"].asBoolean,
                    editorScheme = o["editorScheme"].asString,
                    roles = parseRoles(o.getAsJsonObject("roles")),
                    keywords = o.getAsJsonObject("keywords")?.let(::parseKeywords),
                    defaultForeground = o["defaultForeground"]?.asString,
                    foregrounds = o.getAsJsonObject("foregrounds")?.entrySet()?.associate { (level, f) ->
                        val foreground = f.asJsonObject
                        level to Foreground(parseRoles(foreground.getAsJsonObject("roles")), foreground.getAsJsonObject("keywords")?.let(::parseKeywords))
                    }.orEmpty(),
                    paletteFamily = o["family"]?.asString ?: "material",
                    levels = o.getAsJsonArray("foregroundLevels")?.map { it.asJsonObject.let { l -> Level(l["id"].asString, l["label"].asString) } }.orEmpty(),
                )
            }
            val g = JsonParser.parseString(groupsJson).asJsonObject
            fun list(name: String) = g.strings(name)
            val schemeRoles = g.getAsJsonObject("schemeForegroundRoles")?.entrySet()?.associate { (family, r) ->
                val roles = r.asJsonObject
                family to SchemeRoles(
                    roles.getAsJsonObject("colors")?.stringMap().orEmpty(),
                    roles.getAsJsonObject("attributes")?.entrySet()?.associate { (key, fields) -> key to fields.asJsonObject.stringMap() }.orEmpty(),
                )
            }.orEmpty()
            val uiKeys = g.getAsJsonObject("uiForegroundKeys")?.entrySet()?.associate { (family, roles) ->
                family to roles.asJsonObject.entrySet().associate { (role, keys) -> role to keys.asJsonArray.map { it.asString } }
            }.orEmpty()
            val accentKeys = g.getAsJsonObject("accentUiKeys")?.entrySet()?.associate { (family, keys) -> family to keys.asJsonArray.map { it.asString } }.orEmpty()
            val keyGroups = g.getAsJsonObject("keyGroups")?.entrySet()?.associate { (family, lists) ->
                family to lists.asJsonObject.entrySet().associate { (name, keys) -> name to keys.asJsonArray.map { it.asString } }
            }.orEmpty()
            val styles = g.getAsJsonObject("styles")?.entrySet()?.associate { (family, s) ->
                val o = s.asJsonObject
                family to Styles(o.strings("bold"), o.strings("italic"), o["shipped"].asBoolean)
            }.orEmpty()
            val accentRole = g.getAsJsonObject("accentRole")?.stringMap().orEmpty()
            val highUi = g.getAsJsonObject("highUiContrast")?.entrySet()?.associate { (family, keys) -> family to keys.asJsonObject.entrySet().associate { (key, step) -> key to step.asJsonObject.let { RoleStep(it["from"].asString, it["to"].asString) } } }.orEmpty()
            return Palette(
                variants,
                Groups(
                    list("operators"), list("comments"), list("docs"), list("calls"), accentKeys, list("keywords"), list("parameters"), list("reassigned"), list("annotations"),
                    schemeRoles, uiKeys, highUi, keyGroups, styles, accentRole,
                ),
            )
        }

        fun load(): Palette = parse(resource("/gruvbox/palette.json"), resource("/gruvbox/groups.json"))

        private fun resource(path: String) = Palette::class.java.getResource(path)!!.readText()

        private fun parseKeywords(o: JsonObject) = KeywordTable(
            brightness = o.strings("brightness"),
            strength = o.strings("strength"),
            families = o.getAsJsonObject("families").entrySet().associate { (id, f) ->
                val family = f.asJsonObject
                id to KeywordFamily(family["label"].asString, family.getAsJsonArray("colors").map { row -> row.asJsonArray.map { parseColor(it.asString) } })
            },
        )

        private fun JsonObject.strings(name: String) = getAsJsonArray(name)?.map { it.asString }.orEmpty()

        private fun JsonObject.stringMap() = entrySet().associate { (k, v) -> k to v.asString }

        private fun parseRoles(o: JsonObject) = o.entrySet().associate { (role, hex) -> role to parseColor(hex.asString) }

        /** `#rrggbb` or `#rrggbbaa`. */
        fun parseColor(hex: String): Color {
            val v = hex.removePrefix("#")
            val rgb = v.substring(0, 6).toInt(16)
            return if (v.length == 8) Color((v.substring(6, 8).toInt(16) shl 24) or rgb, true) else Color(rgb)
        }
    }
}
