package dev.gipo.gruvboxmaterial.settings

import java.awt.Color
import java.awt.Window
import javax.swing.UIDefaults
import javax.swing.UIManager
import javax.swing.plaf.ColorUIResource

/** Text contrast, accent and tab style as UIManager overrides on top of the installed theme, restorable while the same LaF is installed. */
class UiOverrides {
    private var defaults: UIDefaults? = null
    private val originals = LinkedHashMap<String, Any?>()
    private val wildcardOriginals = LinkedHashMap<String, Any?>()

    /** Applies text contrast [level], [accent] and [tabStyle] for [variant], or only restores when [variant] is null (another LaF is active). */
    fun apply(variant: Variant?, level: String?, groups: Groups, accent: String, tabStyle: TabStyle) {
        val current = UIManager.getLookAndFeelDefaults()
        // A LaF change rebuilds the defaults, so the old originals belong to a table nobody reads anymore.
        if (current === defaults) restoreValues(current) else forget()
        defaults = current
        if (variant != null) {
            val base = variant.atLevel(null).roles
            val roles = variant.atLevel(level).roles
            for ((role, keys) in groups.uiForegroundKeys[variant.schemeFamily].orEmpty()) recolor(current, keys, base[role], roles[role])
            recolor(current, groups.accentUiKeys[variant.schemeFamily].orEmpty(), roles["aqua"], roles[accent])
            if (tabStyle == TabStyle.FILLED) fillTabs(current, roles)
        }
        repaintAll()
    }

    fun restore() {
        defaults?.takeIf { it === UIManager.getLookAndFeelDefaults() }?.let { restoreValues(it) }
        forget()
        repaintAll()
    }

    // Matches on rgb and keeps each value's own alpha, so translucent uses of a role follow it.
    private fun recolor(current: UIDefaults, keys: List<String>, from: Color?, to: Color?) {
        if (from == null || to == null || sameColor(from, to)) return
        val names = current.keys.filterIsInstance<String>()
        for (key in keys) {
            if (key.startsWith("*.")) {
                val suffix = key.substring(1)
                names.filter { it.endsWith(suffix) && sameColor(current[it], from) }.forEach { put(current, it, withAlpha(to, current[it] as Color)) }
                recolorWildcard(current, suffix.removePrefix("."), from, to)
            } else if (sameColor(current[key], from)) {
                put(current, key, withAlpha(to, current[key] as Color))
            }
        }
    }

    // Keys the theme only sets through "*" are resolved by JBColor from the "*" map, cached in "*cache".
    @Suppress("UNCHECKED_CAST")
    private fun recolorWildcard(current: UIDefaults, suffix: String, from: Color, to: Color) {
        val map = current["*"] as? MutableMap<Any?, Any?> ?: return
        for (k in map.keys.filterIsInstance<String>()) {
            if (k.removePrefix(".") != suffix || !sameColor(map[k], from)) continue
            if (k !in wildcardOriginals) wildcardOriginals[k] = map[k]
            map[k] = ColorUIResource(withAlpha(to, map[k] as Color))
        }
        (current["*cache"] as? MutableMap<*, *>)?.clear()
    }

    // Islands paints the selected tab as a fill of underlinedTabBackground outlined by underlinedBorderColor;
    // "filled" drops the outline into the fill.
    private fun fillTabs(current: UIDefaults, roles: Map<String, Color>) {
        val active = roles["bg3"] ?: return
        val inactive = roles["bg_current_word"] ?: return
        put(current, "EditorTabs.underlinedTabBackground", active)
        put(current, "EditorTabs.underlinedBorderColor", active)
        put(current, "EditorTabs.inactiveUnderlinedTabBackground", inactive)
        put(current, "EditorTabs.inactiveUnderlinedTabBorderColor", inactive)
    }

    private fun put(current: UIDefaults, key: String, color: Color) {
        if (key !in originals) originals[key] = current[key]
        current[key] = ColorUIResource(color)
    }

    @Suppress("UNCHECKED_CAST")
    private fun restoreValues(current: UIDefaults) {
        for ((key, value) in originals) current[key] = value
        val map = current["*"] as? MutableMap<Any?, Any?>
        if (map != null) for ((key, value) in wildcardOriginals) map[key] = value
        (current["*cache"] as? MutableMap<*, *>)?.clear()
        forget()
    }

    private fun forget() {
        originals.clear()
        wildcardOriginals.clear()
    }

    private fun sameColor(value: Any?, color: Color) = value is Color && value.rgb and 0xffffff == color.rgb and 0xffffff

    private fun withAlpha(color: Color, alphaOf: Color) = Color(color.rgb and 0xffffff or (alphaOf.alpha shl 24), true)

    private fun repaintAll() = Window.getWindows().forEach { it.repaint() }
}
