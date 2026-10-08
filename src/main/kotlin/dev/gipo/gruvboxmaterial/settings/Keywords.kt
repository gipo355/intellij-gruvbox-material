package dev.gipo.gruvboxmaterial.settings

import java.awt.Color
import kotlin.math.pow

const val STOCK = "stock"
const val PLAIN = "plain"

val KEYWORD_FAMILIES = listOf(STOCK, "red", "orange", "clay", "stone", "slate", PLAIN)

/** Keyword families whose hue clashes with the orange operators, which then move to fg0. */
val OPERATOR_CLASHING_FAMILIES = setOf("red", "orange", "clay")

data class KeywordChoice(val family: String = STOCK, val brightness: Int = 1, val strength: Int = 1) {
    /** Brightness and strength only pick from a family's table; stock and plain have none. */
    val tunable get() = family != STOCK && family != PLAIN
}

/** The keyword colour [choice] picks in [variant], or null for stock or a family, row or column the variant does not ship. */
fun keywordColor(variant: Variant, choice: KeywordChoice): Color? = when (choice.family) {
    STOCK -> null
    PLAIN -> variant.roles["fg0"]
    else -> variant.keywords?.families?.get(choice.family)?.colors?.getOrNull(choice.brightness)?.getOrNull(choice.strength)
}

fun keywordFamilyLabel(variant: Variant?, family: String): String =
    variant?.keywords?.families?.get(family)?.label ?: family.replaceFirstChar(Char::uppercase)

/** WCAG 2 contrast ratio, 1 to 21. */
fun contrastRatio(a: Color, b: Color): Double {
    val la = luminance(a)
    val lb = luminance(b)
    return (maxOf(la, lb) + 0.05) / (minOf(la, lb) + 0.05)
}

private fun luminance(c: Color): Double {
    fun channel(v: Int) = (v / 255.0).let { if (it <= 0.03928) it / 12.92 else ((it + 0.055) / 1.055).pow(2.4) }
    return 0.2126 * channel(c.red) + 0.7152 * channel(c.green) + 0.0722 * channel(c.blue)
}
