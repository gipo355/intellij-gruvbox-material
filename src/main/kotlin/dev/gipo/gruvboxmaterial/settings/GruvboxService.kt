package dev.gipo.gruvboxmaterial.settings

import com.intellij.ide.ui.LafManager
import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.options.Scheme

/** Applies the settings on top of the shipped theme and puts everything back when toggled off or unloaded. */
@Service(Service.Level.APP)
class GruvboxService : Disposable {
    val palette: Palette by lazy { Palette.load() }
    private val schemeOverrides = SchemeOverrides()
    private val uiOverrides = UiOverrides()
    private var refreshing = false
    private var started = false

    private val state get() = GruvboxSettings.getInstance().state

    /** The variant whose LaF is installed, or null when another theme is active. */
    fun activeVariant(): Variant? = LafManager.getInstance().currentUIThemeLookAndFeel?.id?.let { palette.variants[it] }

    fun installedVariants(): List<Variant> = palette.variants.values.filter { findLaf(it.id) != null }

    fun switchVariant(id: String) {
        val laf = LafManager.getInstance()
        if (laf.currentUIThemeLookAndFeel?.id == id) return
        val target = findLaf(id) ?: return
        laf.setCurrentLookAndFeel(target, false)
        laf.updateUI()
    }

    private fun findLaf(id: String) = LafManager.getInstance().installedThemes.firstOrNull { it.id == id }

    fun startOnce() {
        if (started) return
        started = true
        applyAll()
    }

    fun applyAll() {
        applyScheme()
        applyUi()
        IndentRainbowSync.getInstance()?.apply(activeVariant(), state.indentRainbowSync)
    }

    fun applyScheme() {
        if (refreshing) return
        val hadOverrides = !schemeOverrides.isEmpty
        schemeOverrides.restore()
        val scheme = EditorColorsManager.getInstance().globalScheme
        val variant = palette.variantForScheme(scheme.name.removePrefix(Scheme.EDITABLE_COPY_PREFIX))
        val readability = state.readability
        val keywords = state.keywords
        val keywordColor = variant?.let { keywordColor(it, keywords) }
        if (variant != null && (readability.any || keywordColor != null)) {
            val groups = palette.groups
            val keys = groups.operators + groups.comments + groups.docs + groups.calls + groups.keywords + groups.parameters + groups.reassigned + groups.annotations
            schemeOverrides.apply(scheme, readabilityOverrides(directlyDefined(scheme, keys), groups, variant.roles, readability, keywordColor, keywords.family))
        }
        if (hadOverrides || !schemeOverrides.isEmpty) refreshEditors(scheme)
    }

    fun applyUi() = uiOverrides.apply(activeVariant(), palette.groups.accentUiKeys, state.accent ?: "aqua", state.tabStyle)

    /** Puts the shipped scheme values back so a settings save never sees the overrides. */
    fun restoreScheme() {
        if (schemeOverrides.isEmpty) return
        schemeOverrides.restore()
        refreshEditors(EditorColorsManager.getInstance().globalScheme)
    }

    private fun refreshEditors(scheme: EditorColorsScheme) {
        refreshing = true
        try {
            // Listeners (ours guarded by `refreshing`) re-read the scheme; refreshAllEditors repaints open editors.
            ApplicationManager.getApplication().messageBus.syncPublisher(EditorColorsManager.TOPIC).globalSchemeChange(scheme)
            EditorFactory.getInstance().refreshAllEditors()
        } finally {
            refreshing = false
        }
    }

    override fun dispose() {
        try {
            restoreScheme()
            uiOverrides.restore()
        } catch (e: Exception) {
            thisLogger().warn("Could not restore the shipped theme values", e)
        }
    }

    companion object {
        fun getInstance(): GruvboxService = service()
    }
}
