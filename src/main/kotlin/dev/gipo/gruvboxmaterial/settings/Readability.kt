package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.colors.impl.AbstractColorsScheme
import com.intellij.openapi.editor.markup.TextAttributes
import java.awt.Color
import java.util.IdentityHashMap

data class Readability(
    val quietOperators: Boolean = false,
    val dimComments: Boolean = false,
    val softenDocs: Boolean = false,
    val emphasizeDeclarations: Boolean = false,
) {
    val any get() = quietOperators || dimComments || softenDocs || emphasizeDeclarations
}

/**
 * The attributes the enabled toggles replace, keyed by attribute name: [original] attributes with only the foreground
 * changed. Keys missing from [original] are skipped, so only attributes the scheme defines itself are touched.
 */
fun readabilityOverrides(
    original: Map<String, TextAttributes>,
    groups: Groups,
    roles: Map<String, Color>,
    readability: Readability,
): Map<String, TextAttributes> {
    val result = LinkedHashMap<String, TextAttributes>()
    fun recolor(keys: List<String>, color: Color?) {
        if (color == null) return
        for (key in keys) {
            val attributes = original[key] ?: continue
            if (attributes.foregroundColor != color) result[key] = attributes.clone().apply { foregroundColor = color }
        }
    }
    if (readability.quietOperators) recolor(groups.operators, roles["grey2"])
    if (readability.dimComments) recolor(groups.comments, roles["grey1"])
    if (readability.softenDocs) {
        val commentColor = if (readability.dimComments) roles["grey1"] else groups.comments.firstNotNullOfOrNull { original[it]?.foregroundColor }
        recolor(groups.docs, commentColor)
    }
    if (readability.emphasizeDeclarations) recolor(groups.calls, roles["fg0"])
    return result
}

/** The attributes [scheme] defines itself for [names]; inherited attributes are left out. */
fun directlyDefined(scheme: EditorColorsScheme, names: Collection<String>): Map<String, TextAttributes> =
    names.mapNotNull { name ->
        val key = TextAttributesKey.find(name)
        val attributes = if (scheme is AbstractColorsScheme) scheme.getDirectlyDefinedAttributes(key) else scheme.getAttributes(key)
        attributes?.let { name to it }
    }.toMap()

/** Writes overrides into live schemes in memory and puts back the exact original objects on [restore]. */
class SchemeOverrides {
    private val originals = IdentityHashMap<EditorColorsScheme, MutableMap<TextAttributesKey, TextAttributes?>>()

    val isEmpty get() = originals.isEmpty()

    fun apply(scheme: EditorColorsScheme, overrides: Map<String, TextAttributes>) {
        if (overrides.isEmpty()) return
        val saved = originals.getOrPut(scheme) { LinkedHashMap() }
        for ((name, attributes) in overrides) {
            val key = TextAttributesKey.find(name)
            if (key !in saved) saved[key] = (scheme as? AbstractColorsScheme)?.getDirectlyDefinedAttributes(key) ?: scheme.getAttributes(key)
            scheme.setAttributes(key, attributes)
        }
    }

    fun restore() {
        for ((scheme, saved) in originals) {
            for ((key, attributes) in saved) if (attributes != null) scheme.setAttributes(key, attributes)
        }
        originals.clear()
    }
}
