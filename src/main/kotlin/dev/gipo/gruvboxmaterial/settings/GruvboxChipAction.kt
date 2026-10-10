package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.DefaultActionGroup
import com.intellij.openapi.actionSystem.Separator
import com.intellij.openapi.project.DumbAwareAction
import com.intellij.openapi.project.DumbAwareToggleAction
import com.intellij.openapi.ui.popup.JBPopupFactory
import kotlin.reflect.KMutableProperty1

/** Main toolbar chip, visible only under one of our themes: variants, readability toggles, accent, keywords and reading font. */
class GruvboxChipAction : DumbAwareAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT

    override fun update(e: AnActionEvent) {
        e.presentation.isEnabledAndVisible = GruvboxService.getInstance().activeVariant() != null
    }

    override fun actionPerformed(e: AnActionEvent) {
        val popup = JBPopupFactory.getInstance()
            .createActionGroupPopup("Gruvbox Material", popupGroup(), e.dataContext, JBPopupFactory.ActionSelectionAid.SPEEDSEARCH, true)
        val component = e.inputEvent?.component
        if (component != null) popup.showUnderneathOf(component) else popup.showInBestPositionFor(e.dataContext)
    }

    private fun popupGroup() = DefaultActionGroup().apply {
        val service = GruvboxService.getInstance()
        val variants = service.installedVariants()
        if (variants.size > 1) {
            for (variant in variants) add(Choice(variant.name, { service.activeVariant()?.id == variant.id }) { service.switchVariant(variant.id) })
            add(Separator.create())
        }
        add(ReadabilityToggle("Quiet operators", GruvboxState::quietOperators))
        add(ReadabilityToggle("Keep operator colour", GruvboxState::keepOperatorColor))
        add(ReadabilityToggle("Dim comments", GruvboxState::dimComments))
        add(ReadabilityToggle("Soften doc comments", GruvboxState::softenDocs))
        add(ReadabilityToggle("Emphasize declarations", GruvboxState::emphasizeDeclarations))
        add(ReadabilityToggle("Italic comments", GruvboxState::italicComments))
        add(ReadabilityToggle("Italic parameters", GruvboxState::italicParameters))
        add(ReadabilityToggle("Hide reassignment underline", GruvboxState::hideReassignUnderline))
        add(DefaultActionGroup("Annotations", true).apply {
            for (style in AnnotationStyle.entries) {
                add(Choice(style.label, { state().annotationStyle == style }) {
                    state().annotationStyle = style
                    service.applyScheme()
                })
            }
        })
        add(DefaultActionGroup("Accent", true).apply {
            for (accent in ACCENTS) {
                add(Choice(accent.replaceFirstChar(Char::uppercase), { state().accent == accent }) {
                    state().accent = accent
                    service.applyUi()
                })
            }
        })
        add(DefaultActionGroup("Keywords", true).apply {
            val variant = service.activeVariant()
            for (family in KEYWORD_FAMILIES) {
                add(Choice(keywordFamilyLabel(variant, family), { state().keywords.family == family }) {
                    state().keywordFamily = family
                    service.applyScheme()
                })
            }
            add(Separator.create())
            val rows = variant?.keywords?.brightness?.size ?: 0
            add(Run("Brightness up", { state().keywords.tunable && state().keywordBrightness > 0 }) { stepBrightness(-1) })
            add(Run("Brightness down", { state().keywords.tunable && state().keywordBrightness < rows - 1 }) { stepBrightness(1) })
        })
        add(Separator.create())
        for (preset in ReadingPreset.entries) {
            if (preset.installedFamily() != null) add(Run("Apply reading font: ${preset.label}") { ReadingFont.apply(state(), preset) })
        }
        if (ReadingFont.isApplied(state())) add(Run("Revert reading font") { ReadingFont.revert(state()) })
    }

    // Row 0 is the brightest, so up is towards 0.
    private fun stepBrightness(delta: Int) {
        state().keywordBrightness += delta
        GruvboxService.getInstance().applyScheme()
    }

    private class ReadabilityToggle(text: String, private val property: KMutableProperty1<GruvboxState, Boolean>) : DumbAwareToggleAction(text) {
        override fun getActionUpdateThread() = ActionUpdateThread.EDT
        override fun isSelected(e: AnActionEvent) = property.get(state())
        override fun setSelected(e: AnActionEvent, selected: Boolean) {
            property.set(state(), selected)
            GruvboxService.getInstance().applyScheme()
        }
    }

    private class Choice(text: String, private val selected: () -> Boolean, private val select: () -> Unit) : DumbAwareToggleAction(text) {
        override fun getActionUpdateThread() = ActionUpdateThread.EDT
        override fun isSelected(e: AnActionEvent) = selected()
        override fun setSelected(e: AnActionEvent, state: Boolean) = select()
    }

    private class Run(text: String, private val enabled: () -> Boolean = { true }, private val run: () -> Unit) : DumbAwareAction(text) {
        override fun getActionUpdateThread() = ActionUpdateThread.EDT
        override fun update(e: AnActionEvent) {
            e.presentation.isEnabled = enabled()
        }
        override fun actionPerformed(e: AnActionEvent) = run()
    }
}

private fun state() = GruvboxSettings.getInstance().state
