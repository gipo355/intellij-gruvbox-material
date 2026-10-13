package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service

enum class TabStyle { UNDERLINE, FILLED }

/** Accent choices per palette family; the first is the one its theme ships. */
val ACCENTS = mapOf(
    "material" to listOf("aqua", "green", "yellow", "orange", "tan", "purple", "red"),
    "baby" to listOf("blue", "aqua", "green", "yellow", "orange", "purple", "red"),
)

fun accentChoices(variant: Variant?): List<String> = ACCENTS[variant?.paletteFamily] ?: ACCENTS.getValue("material")

class GruvboxState : BaseState() {
    // Text contrast level id per palette family; a missing or unknown id follows the variant's default.
    var textContrasts by map<String, String>()
    var highUiContrast by property(false)
    var quietOperators by property(false)
    var keepOperatorColor by property(true)
    var dimComments by property(false)
    var softenDocs by property(false)
    var emphasizeDeclarations by property(false)
    var italicComments by property(false)
    var italicParameters by property(false)
    var hideReassignUnderline by property(false)
    var annotationStyle by enum(AnnotationStyle.PURPLE)
    // Material's accent from before accents were kept per palette family; read only while accents has no material entry.
    var accent by string("aqua")
    var accents by map<String, String>()
    // Bold and Italic per palette family; a missing entry follows what the family's scheme ships.
    var bold by map<String, Boolean>()
    var italic by map<String, Boolean>()
    var tabStyle by enum(TabStyle.UNDERLINE)
    var indentRainbowSync by property(false)
    var keywordFamily by string(STOCK)
    var keywordBrightness by property(1)
    var keywordStrength by property(1)

    // The user's Indent Rainbow palette before sync took over; null while sync is not applied.
    var irPaletteType by string()
    var irCustomPalette by string()
    var irNumberColors by property(0)

    // The editor font before the reading preset; null while the preset is not applied.
    var fontFamily by string()
    var fontSecondaryFamily by string()
    var fontSize by property(0f)
    var fontLineSpacing by property(0f)
    var fontRegularSubFamily by string()
    var fontBoldSubFamily by string()
    var fontLigatures by property(false)
    var fontVariants by stringSet()

    val readability get() = Readability(quietOperators, dimComments, softenDocs, emphasizeDeclarations, italicComments, italicParameters, hideReassignUnderline, annotationStyle, keepOperatorColor)
    val keywords get() = KeywordChoice(keywordFamily ?: STOCK, keywordBrightness, keywordStrength)

    /** The level chosen for [variant]'s palette family, or null for the variant's default. */
    fun textContrast(variant: Variant?): String? = variant?.level(textContrasts[variant.paletteFamily])

    fun setTextContrast(variant: Variant, level: String?) {
        if (level == null) textContrasts.remove(variant.paletteFamily) else textContrasts[variant.paletteFamily] = level
    }

    /** The accent chosen for [variant]'s palette family; unset or not one of its choices is the shipped one. */
    fun accent(variant: Variant?): String {
        val choices = accentChoices(variant)
        val family = variant?.paletteFamily ?: "material"
        val stored = accents[family] ?: accent.takeIf { family == "material" }
        return stored?.takeIf { it in choices } ?: choices.first()
    }

    fun setAccent(variant: Variant?, accent: String) {
        accents[variant?.paletteFamily ?: "material"] = accent
    }

    fun isBold(variant: Variant, groups: Groups): Boolean = bold[variant.paletteFamily] ?: groups.shipsStyles(variant)

    fun isItalic(variant: Variant, groups: Groups): Boolean = italic[variant.paletteFamily] ?: groups.shipsStyles(variant)

    fun setBold(variant: Variant, groups: Groups, on: Boolean) {
        if (on == groups.shipsStyles(variant)) bold.remove(variant.paletteFamily) else bold[variant.paletteFamily] = on
    }

    fun setItalic(variant: Variant, groups: Groups, on: Boolean) {
        if (on == groups.shipsStyles(variant)) italic.remove(variant.paletteFamily) else italic[variant.paletteFamily] = on
    }
}

@Service(Service.Level.APP)
@State(name = "GruvboxMaterialSettings", storages = [Storage("gruvbox-material.xml")])
class GruvboxSettings : SimplePersistentStateComponent<GruvboxState>(GruvboxState()) {
    companion object {
        fun getInstance(): GruvboxSettings = service()
    }
}
