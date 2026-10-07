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
)

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
    val accentUiKeys: List<String>,
    val keywords: List<String> = emptyList(),
)

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
                    roles = o.getAsJsonObject("roles").entrySet().associate { (role, hex) -> role to parseColor(hex.asString) },
                    keywords = o.getAsJsonObject("keywords")?.let(::parseKeywords),
                )
            }
            val g = JsonParser.parseString(groupsJson).asJsonObject
            fun list(name: String) = g.strings(name)
            return Palette(variants, Groups(list("operators"), list("comments"), list("docs"), list("calls"), list("accentUiKeys"), list("keywords")))
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

        /** `#rrggbb` or `#rrggbbaa`. */
        fun parseColor(hex: String): Color {
            val v = hex.removePrefix("#")
            val rgb = v.substring(0, 6).toInt(16)
            return if (v.length == 8) Color((v.substring(6, 8).toInt(16) shl 24) or rgb, true) else Color(rgb)
        }
    }
}
