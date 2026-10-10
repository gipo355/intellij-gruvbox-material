package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.colors.impl.AbstractColorsScheme
import com.intellij.openapi.editor.markup.TextAttributes
import java.awt.Color
import java.awt.Font
import java.util.IdentityHashMap

data class Readability(
    val quietOperators: Boolean = false,
    val dimComments: Boolean = false,
    val softenDocs: Boolean = false,
    val emphasizeDeclarations: Boolean = false,
    val italicComments: Boolean = false,
    val italicParameters: Boolean = false,
    val hideReassignUnderline: Boolean = false,
    val annotations: AnnotationStyle = AnnotationStyle.PURPLE,
    val keepOperatorColor: Boolean = true,
) {
    val any get() = quietOperators || dimComments || softenDocs || emphasizeDeclarations || italicComments || italicParameters || hideReassignUnderline ||
        annotations != AnnotationStyle.PURPLE
}

/** The colour of annotation and decorator names; their attribute names keep fg0. */
enum class AnnotationStyle(val label: String) {
    PURPLE("Purple"),
    GREY("Grey"),
    DIM_GREY("Dim grey"),
    KEYWORD("Keyword colour"),
}

/**
 * The attributes the enabled toggles and [keywordColor] replace, keyed by attribute name: clones of [original] with the
 * foreground, the font style or the reassignment underline changed. Keys missing from [original] are skipped, so only
 * attributes the scheme defines itself are touched. [keywordFamily] is the family [keywordColor] comes from.
 */
fun readabilityOverrides(
    original: Map<String, TextAttributes>,
    groups: Groups,
    roles: Map<String, Color>,
    readability: Readability,
    keywordColor: Color? = null,
    keywordFamily: String = STOCK,
): Map<String, TextAttributes> {
    val result = LinkedHashMap<String, TextAttributes>()
    // Each change builds on the earlier ones for the same key, so toggles touching one key combine.
    fun change(keys: List<String>, edit: TextAttributes.() -> Unit) {
        for (key in keys) {
            val base = original[key] ?: continue
            val changed = (result[key] ?: base).clone().apply(edit)
            if (changed != base) result[key] = changed else result.remove(key)
        }
    }
    fun recolor(keys: List<String>, color: Color?) {
        if (color != null) change(keys) { foregroundColor = color }
    }
    // Unless kept, operators step aside to fg0 for keyword hues that clash with their orange; quiet still wins.
    if (readability.quietOperators) recolor(groups.operators, roles["grey2"])
    else if (!readability.keepOperatorColor && keywordColor != null && keywordFamily in OPERATOR_CLASHING_FAMILIES) recolor(groups.operators, roles["fg0"])
    recolor(groups.keywords, keywordColor)
    if (readability.dimComments) recolor(groups.comments, roles["grey1"])
    if (readability.softenDocs) {
        val commentColor = if (readability.dimComments) roles["grey1"] else groups.comments.firstNotNullOfOrNull { original[it]?.foregroundColor }
        recolor(groups.docs, commentColor)
    }
    if (readability.emphasizeDeclarations) recolor(groups.calls, roles["fg0"])
    when (readability.annotations) {
        AnnotationStyle.PURPLE -> {}
        AnnotationStyle.GREY -> recolor(groups.annotations, roles["grey2"])
        AnnotationStyle.DIM_GREY -> recolor(groups.annotations, roles["grey1"])
        AnnotationStyle.KEYWORD -> recolor(groups.annotations, keywordColor ?: original["DEFAULT_KEYWORD"]?.foregroundColor)
    }
    if (readability.italicComments) change(groups.comments + groups.docs) { fontType = fontType or Font.ITALIC }
    if (readability.italicParameters) change(groups.parameters) { fontType = fontType or Font.ITALIC }
    if (readability.hideReassignUnderline) change(groups.reassigned) {
        effectType = null
        effectColor = null
    }
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
