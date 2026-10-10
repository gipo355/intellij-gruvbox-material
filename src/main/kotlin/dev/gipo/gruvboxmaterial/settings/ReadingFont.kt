package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.editor.colors.FontPreferences
import com.intellij.openapi.editor.colors.ModifiableFontPreferences
import com.intellij.openapi.editor.colors.impl.AppEditorFontOptions
import com.intellij.openapi.editor.colors.impl.FontPreferencesImpl
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.application.ApplicationManager
import java.awt.GraphicsEnvironment

/** A font with glyph variants tuned for reading under blur; [summary] says what the variants change. */
enum class ReadingPreset(val label: String, private val families: List<String>, val characterVariants: Set<String>, val summary: String) {
    // Maximal disambiguation of look-alike glyphs (l/1/I, 0/O, g/q, rn/m) under blur;
    // ligatures stay on but are broken into countable parts.
    MAPLE(
        "Maple Mono", listOf("Maple Mono NF", "Maple Mono"),
        setOf("zero", "cv01", "cv02", "cv03", "cv04", "cv05", "cv08", "cv62", "cv64", "ss01", "ss02", "ss04", "ss05"),
        "glyph variants that keep l/1/I, 0/O and g/q apart",
    ),

    // The stock 0 is already dotted and 1/I already differ; cv03 two-storey g, never q; cv05 round-tailed l, never 1;
    // cv10 r with a foot, so rn never reads as m; ss19 splits == and === so the = can be counted.
    JETBRAINS_MONO(
        "JetBrains Mono", listOf("JetBrains Mono"),
        setOf("cv03", "cv05", "cv10", "ss19"),
        "two-storey g, round-tailed l, footed r, split == and ===",
    );

    fun installedFamily(): String? {
        val names = GraphicsEnvironment.getLocalGraphicsEnvironment().availableFontFamilyNames.toSet()
        return families.firstOrNull { it in names }
    }
}

/** Applies a [ReadingPreset] to the app editor font and restores the font it replaced. */
object ReadingFont {
    const val LINE_SPACING = 1.3f

    fun isApplied(state: GruvboxState) = state.fontFamily != null

    fun apply(state: GruvboxState, preset: ReadingPreset) {
        val family = preset.installedFamily() ?: return
        val current = AppEditorFontOptions.getInstance().fontPreferences
        if (!isApplied(state)) snapshot(current, state)
        val size = current.getSize2D(current.fontFamily)
        update(FontPreferencesImpl().apply {
            register(family, size)
            regularSubFamily = "Regular"
            lineSpacing = LINE_SPACING
            setUseLigatures(true)
            characterVariants = preset.characterVariants
            current.realFontFamilies.getOrNull(1)?.let { register(it, size) }
        })
    }

    fun revert(state: GruvboxState) {
        val family = state.fontFamily ?: return
        // Mirrors how AppFontOptions loads its persisted state.
        update(FontPreferencesImpl().apply {
            register(family, state.fontSize)
            regularSubFamily = state.fontRegularSubFamily
            boldSubFamily = state.fontBoldSubFamily
            lineSpacing = state.fontLineSpacing
            setUseLigatures(state.fontLigatures)
            characterVariants = state.fontVariants.toSet()
            state.fontSecondaryFamily?.let { register(it, state.fontSize) }
        })
        state.fontFamily = null
        state.fontSecondaryFamily = null
        state.fontSize = 0f
        state.fontLineSpacing = 0f
        state.fontLigatures = false
        state.fontRegularSubFamily = null
        state.fontBoldSubFamily = null
        state.fontVariants.clear()
    }

    private fun snapshot(current: FontPreferences, state: GruvboxState) {
        state.fontFamily = current.fontFamily
        state.fontSecondaryFamily = current.realFontFamilies.getOrNull(1)
        state.fontSize = current.getSize2D(current.fontFamily)
        state.fontLineSpacing = current.lineSpacing
        state.fontRegularSubFamily = current.regularSubFamily
        state.fontBoldSubFamily = current.boldSubFamily
        state.fontLigatures = current.useLigatures()
        state.fontVariants.clear()
        state.fontVariants.addAll(current.characterVariants)
    }

    private fun update(preferences: ModifiableFontPreferences) {
        AppEditorFontOptions.getInstance().update(preferences)
        ApplicationManager.getApplication().messageBus.syncPublisher(EditorColorsManager.TOPIC)
            .globalSchemeChange(EditorColorsManager.getInstance().globalScheme)
        EditorFactory.getInstance().refreshAllEditors()
    }
}
