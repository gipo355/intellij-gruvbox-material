package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.ColorKey
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.impl.AbstractColorsScheme
import com.intellij.openapi.editor.markup.TextAttributes
import java.awt.Color

/**
 * The attributes [variant]'s text contrast level and the readability toggles replace, for [original] the attributes the
 * scheme defines itself. [base] is the same variant at its default level, the one the scheme ships. The toggles build on
 * the swapped attributes, so they compare against and recolour with the level's colours.
 */
fun attributeOverrides(
    original: Map<String, TextAttributes>,
    groups: Groups,
    base: Variant,
    variant: Variant,
    readability: Readability,
    keywords: KeywordChoice,
): Map<String, TextAttributes> {
    val swapped = foregroundOverrides(original, groups.schemeForegroundRoles[base.family]?.attributes.orEmpty(), base.roles, variant.roles)
    return swapped + readabilityOverrides(original + swapped, groups, variant.roles, readability, keywordColor(variant, keywords), keywords.family)
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
    for ((key, role) in groups.schemeForegroundRoles[base.family]?.colors.orEmpty()) {
        val color = original[key] ?: continue
        val new = variant.roles[role] ?: continue
        if (color == base.roles[role] && new != color) result[key] = new
    }
    if (highUiContrast) {
        for ((key, step) in groups.highUiContrast[base.family].orEmpty()) {
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
