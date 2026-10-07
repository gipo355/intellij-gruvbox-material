package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.DefaultActionGroup
import com.intellij.openapi.actionSystem.Separator
import com.intellij.openapi.project.DumbAwareAction
import com.intellij.openapi.project.DumbAwareToggleAction
import com.intellij.openapi.ui.popup.JBPopupFactory
import kotlin.reflect.KMutableProperty1

/** Main toolbar chip, visible only under one of our themes: variants, readability toggles, accent and reading font. */
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
        add(ReadabilityToggle("Dim comments", GruvboxState::dimComments))
        add(ReadabilityToggle("Soften doc comments", GruvboxState::softenDocs))
        add(ReadabilityToggle("Emphasize declarations", GruvboxState::emphasizeDeclarations))
        add(DefaultActionGroup("Accent", true).apply {
            for (accent in ACCENTS) {
                add(Choice(accent.replaceFirstChar(Char::uppercase), { state().accent == accent }) {
                    state().accent = accent
                    service.applyUi()
                })
            }
        })
        add(Separator.create())
        if (ReadingFont.installedFamily() != null) add(Run("Apply reading font") { ReadingFont.apply(state()) })
        if (ReadingFont.isApplied(state())) add(Run("Revert reading font") { ReadingFont.revert(state()) })
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

    private class Run(text: String, private val run: () -> Unit) : DumbAwareAction(text) {
        override fun getActionUpdateThread() = ActionUpdateThread.EDT
        override fun actionPerformed(e: AnActionEvent) = run()
    }
}

private fun state() = GruvboxSettings.getInstance().state
