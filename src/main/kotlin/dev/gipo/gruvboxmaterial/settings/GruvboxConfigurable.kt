package dev.gipo.gruvboxmaterial.settings

import com.intellij.codeInsight.CodeInsightSettings
import com.intellij.openapi.options.BoundConfigurable
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.bind
import com.intellij.ui.dsl.builder.bindItem
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.panel

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
            row {
                checkBox("Current-scope gutter line").bindSelected(CodeInsightSettings.getInstance()::HIGHLIGHT_SCOPE)
                    .comment("The platform's \"Highlight on caret movement: current scope\"")
            }
        }
        group("Interface") {
            row("Accent:") { comboBox(ACCENTS).bindItem({ state.accent ?: "aqua" }, { state.accent = it ?: "aqua" }) }
            buttonsGroup("Selected editor tab:") {
                row {
                    radioButton("Underline", TabStyle.UNDERLINE)
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

    override fun apply() {
        super.apply()
        service.applyAll()
        variantId?.let { service.switchVariant(it) }
    }
}
