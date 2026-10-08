package dev.gipo.gruvboxmaterial.settings

import com.intellij.codeInsight.CodeInsightSettings
import com.intellij.openapi.options.BoundConfigurable
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.Panel
import com.intellij.ui.dsl.builder.bind
import com.intellij.ui.dsl.builder.bindItem
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.panel
import com.intellij.ui.dsl.builder.toNullableProperty
import com.intellij.ui.dsl.listCellRenderer.textListCellRenderer
import com.intellij.util.ui.ColorIcon
import javax.swing.JComponent
import javax.swing.JLabel

class GruvboxConfigurable : BoundConfigurable("Gruvbox Material") {
    private val service = GruvboxService.getInstance()
    private val state = GruvboxSettings.getInstance().state
    private var variantId = service.activeVariant()?.id

    override fun createPanel(): DialogPanel = panel {
        val variants = service.installedVariants()
        if (variants.isNotEmpty()) {
            buttonsGroup("Variant") {
                for (variant in variants) row { radioButton(variant.name, variant.id) }
            }.bind({ variantId ?: "" }, { variantId = it })
        }
        group("Readability") {
            row { checkBox("Quiet operators").bindSelected(state::quietOperators).comment("Operators in grey instead of orange") }
            row { checkBox("Dim comments").bindSelected(state::dimComments) }
            row { checkBox("Soften doc comments").bindSelected(state::softenDocs).comment("Tags, references, markup and code in the comment colour") }
            row { checkBox("Emphasize declarations").bindSelected(state::emphasizeDeclarations).comment("Function calls in the foreground colour; declarations keep theirs") }
            row { checkBox("Italic comments").bindSelected(state::italicComments).comment("Comments and doc comments in italic; the colour still follows the options above") }
            row { checkBox("Italic parameters").bindSelected(state::italicParameters).comment("Parameters in italic; type parameters stay as types") }
            row { checkBox("Hide reassignment underline").bindSelected(state::hideReassignUnderline).comment("Drops the underline on reassigned locals and parameters") }
            row("Annotations:") {
                comboBox(AnnotationStyle.entries, textListCellRenderer { it?.label }).bindItem(state::annotationStyle.toNullableProperty())
                    .comment("Annotation and decorator names; Keyword colour follows the keyword picker. Their arguments keep the text colour")
            }
            row {
                checkBox("Highlight current scope").bindSelected(CodeInsightSettings.getInstance()::HIGHLIGHT_SCOPE)
                    .comment("The platform's \"Highlight on caret movement: current scope\": brightens the enclosing block's indent guide")
            }
            row { comment("Readability and keyword colours live in memory; turn them off before editing this scheme in Editor > Color Scheme, or they may be saved into your copy.") }
        }
        keywordsGroup()
        group("Interface") {
            row("Accent:") { comboBox(ACCENTS).bindItem({ state.accent ?: "aqua" }, { state.accent = it ?: "aqua" }) }
            buttonsGroup("Selected editor tab:") {
                row {
                    radioButton("Outline", TabStyle.UNDERLINE)
                    radioButton("Filled", TabStyle.FILLED)
                }
            }.bind(state::tabStyle)
            if (IndentRainbowSync.getInstance() != null) {
                row { checkBox("Sync Indent Rainbow colours").bindSelected(state::indentRainbowSync).comment("Your own Indent Rainbow palette comes back when this is off") }
            }
        }
        group("Reading Font") {
            val family = ReadingFont.installedFamily()
            row {
                button("Apply Reading Preset") { ReadingFont.apply(state) }.enabled(family != null)
                button("Revert") { ReadingFont.revert(state) }
            }
            row {
                comment(
                    if (family == null) "Maple Mono not installed"
                    else "$family, line spacing ${ReadingFont.LINE_SPACING}, ligatures, glyph variants that keep l/1/I, 0/O and g/q apart. Applies immediately; Revert restores your previous font.",
                )
            }
        }
    }

    private fun Panel.keywordsGroup() {
        val variant = service.activeVariant() ?: service.palette.variants.values.firstOrNull()
        val table = variant?.keywords
        val familyLabels = KEYWORD_FAMILIES.associateWith { keywordFamilyLabel(variant, it) }
        val brightness = table?.brightness.orEmpty()
        val strength = table?.strength.orEmpty()
        lateinit var family: ComboBox<String>
        lateinit var bright: ComboBox<String>
        lateinit var strong: ComboBox<String>
        lateinit var swatch: JLabel
        lateinit var hint: JComponent
        fun choice() = KeywordChoice(
            KEYWORD_FAMILIES.firstOrNull { familyLabels[it] == family.item } ?: STOCK,
            brightness.indexOf(bright.item).coerceAtLeast(0),
            strength.indexOf(strong.item).coerceAtLeast(0),
        )
        fun refresh() {
            val choice = choice()
            bright.isEnabled = choice.tunable
            strong.isEnabled = choice.tunable
            val color = variant?.let { keywordColor(it, choice) }
            val bg = variant?.roles?.get("bg0")
            if (color == null || bg == null) {
                swatch.icon = null
                swatch.text = "Keywords as the scheme ships them"
                hint.isVisible = false
                return
            }
            val ratio = contrastRatio(color, bg)
            swatch.icon = ColorIcon(14, color)
            swatch.text = "#%06x  %.1f:1 on bg0".format(color.rgb and 0xffffff, ratio)
            hint.isVisible = ratio < 4.5
        }
        group("Keywords") {
            row("Family:") {
                family = comboBox(KEYWORD_FAMILIES.map { familyLabels.getValue(it) })
                    .bindItem({ familyLabels[state.keywordFamily] ?: familyLabels.getValue(STOCK) }, { label -> state.keywordFamily = KEYWORD_FAMILIES.firstOrNull { familyLabels[it] == label } ?: STOCK })
                    .component
            }
            row("Brightness:") {
                bright = comboBox(brightness)
                    .bindItem({ brightness.getOrNull(state.keywordBrightness) }, { state.keywordBrightness = brightness.indexOf(it).coerceAtLeast(0) })
                    .component
            }
            row("Strength:") {
                strong = comboBox(strength)
                    .bindItem({ strength.getOrNull(state.keywordStrength) }, { state.keywordStrength = strength.indexOf(it).coerceAtLeast(0) })
                    .component
            }
            row { swatch = label("").component }
            row { hint = comment("Below 4.5:1; Faint and Ghost are meant to recede, so this is a hint, not an error").component }
        }
        for (combo in listOf(family, bright, strong)) combo.addActionListener { refresh() }
        refresh()
    }

    override fun apply() {
        super.apply()
        service.applyAll()
        variantId?.let { service.switchVariant(it) }
    }
}
