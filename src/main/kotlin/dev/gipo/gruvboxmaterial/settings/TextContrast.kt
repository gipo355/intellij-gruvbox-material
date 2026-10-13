package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.ColorKey
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.impl.AbstractColorsScheme
import com.intellij.openapi.editor.markup.TextAttributes
import java.awt.Color
import java.awt.Font

/**
 * The attributes [variant]'s text contrast level, Bold and Italic and the readability toggles replace, for [original]
 * the attributes the scheme defines itself. [base] is the same variant at its default level, the one the scheme ships;
 * null [bold] or [italic] keeps what the scheme ships. Each step builds on the one before, so the toggles compare against
 * and recolour with the level's colours, and Italic comments still applies after Italic is off.
 */
fun attributeOverrides(
    original: Map<String, TextAttributes>,
    groups: Groups,
    base: Variant,
    variant: Variant,
    readability: Readability,
    keywords: KeywordChoice,
    bold: Boolean? = null,
    italic: Boolean? = null,
): Map<String, TextAttributes> {
    val family = groups.forFamily(base.schemeFamily)
    val swapped = foregroundOverrides(original, family.schemeForegroundRoles[base.schemeFamily]?.attributes.orEmpty(), base.roles, variant.roles)
    val styled = swapped + styleOverrides(original + swapped, family.styles[base.schemeFamily], bold, italic)
    return styled + readabilityOverrides(original + styled, family, variant.roles, readability, keywordColor(variant, keywords), keywords.family)
}

/** Clones of [original] with each style set's font bit set or cleared, for a [bold] or [italic] that differs from what [styles] ships. */
fun styleOverrides(original: Map<String, TextAttributes>, styles: Styles?, bold: Boolean?, italic: Boolean?): Map<String, TextAttributes> {
    val result = LinkedHashMap<String, TextAttributes>()
    if (styles == null) return result
    fun set(keys: List<String>, bit: Int, on: Boolean?) {
        if (on == null || on == styles.shipped) return
        for (key in keys) {
            val base = original[key] ?: continue
            val changed = (result[key] ?: base).clone().apply { fontType = if (on) fontType or bit else fontType and bit.inv() }
            if (changed != base) result[key] = changed else result.remove(key)
        }
    }
    set(styles.bold, Font.BOLD, bold)
    set(styles.italic, Font.ITALIC, italic)
    return result
}

/** Clones of [original] with each listed field that holds its role's [from] colour moved to the [to] one. */
fun foregroundOverrides(
    original: Map<String, TextAttributes>,
    fields: Map<String, Map<String, String>>,
    from: Map<String, Color>,
    to: Map<String, Color>,
): Map<String, TextAttributes> {
    val result = LinkedHashMap<String, TextAttributes>()
    for ((key, roles) in fields) {
        val base = original[key] ?: continue
        val changed = base.clone()
        for ((field, role) in roles) {
            val old = from[role] ?: continue
            val new = to[role] ?: continue
            when (field) {
                "FOREGROUND" -> if (changed.foregroundColor == old) changed.foregroundColor = new
                "BACKGROUND" -> if (changed.backgroundColor == old) changed.backgroundColor = new
                "EFFECT_COLOR" -> if (changed.effectColor == old) changed.effectColor = new
                "ERROR_STRIPE_COLOR" -> if (changed.errorStripeColor == old) changed.errorStripeColor = new
            }
        }
        if (changed != base) result[key] = changed
    }
    return result
}

/**
 * The colour keys [variant]'s text contrast level moves off [base]'s role colours, then, with [highUiContrast], the keys
 * still at their shipped role raised a step; colours the user changed stay. Keys missing from [original], the colours the scheme defines itself, are skipped.
 */
fun colorOverrides(original: Map<String, Color>, groups: Groups, base: Variant, variant: Variant, highUiContrast: Boolean): Map<String, Color> {
    val result = LinkedHashMap<String, Color>()
    for ((key, role) in groups.schemeForegroundRoles[base.schemeFamily]?.colors.orEmpty()) {
        val color = original[key] ?: continue
        val new = variant.roles[role] ?: continue
        if (color == base.roles[role] && new != color) result[key] = new
    }
    if (highUiContrast) {
        for ((key, step) in groups.highUiContrast[base.schemeFamily].orEmpty()) {
            if (original[key] != base.roles[step.from]) continue
            result[key] = variant.roles[step.to] ?: continue
        }
    }
    return result
}

/** The colours [scheme] or its parent schemes define for [names], like [directlyDefined]; explicitly empty colours are left out. */
fun directlyDefinedColors(scheme: EditorColorsScheme, names: Collection<String>): Map<String, Color> =
    names.mapNotNull { name ->
        val key = ColorKey.find(name)
        val color = if (scheme is AbstractColorsScheme) scheme.getDirectlyDefinedColor(key) else scheme.getColor(key)
        color?.takeIf { it !== AbstractColorsScheme.NULL_COLOR_MARKER && it !== AbstractColorsScheme.INHERITED_COLOR_MARKER }?.let { name to it }
    }.toMap()
