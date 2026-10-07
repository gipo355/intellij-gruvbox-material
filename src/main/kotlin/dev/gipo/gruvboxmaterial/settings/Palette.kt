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
)

data class Groups(
    val operators: List<String>,
    val comments: List<String>,
    val docs: List<String>,
    val calls: List<String>,
    val accentUiKeys: List<String>,
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
                )
            }
            val g = JsonParser.parseString(groupsJson).asJsonObject
            fun list(name: String) = g.strings(name)
            return Palette(variants, Groups(list("operators"), list("comments"), list("docs"), list("calls"), list("accentUiKeys")))
        }

        fun load(): Palette = parse(resource("/gruvbox/palette.json"), resource("/gruvbox/groups.json"))

        private fun resource(path: String) = Palette::class.java.getResource(path)!!.readText()

        private fun JsonObject.strings(name: String) = getAsJsonArray(name)?.map { it.asString }.orEmpty()

        /** `#rrggbb` or `#rrggbbaa`. */
        fun parseColor(hex: String): Color {
            val v = hex.removePrefix("#")
            val rgb = v.substring(0, 6).toInt(16)
            return if (v.length == 8) Color((v.substring(6, 8).toInt(16) shl 24) or rgb, true) else Color(rgb)
        }
    }
}
