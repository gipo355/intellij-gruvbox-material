package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.thisLogger
import java.awt.Color

private const val PALETTE_TYPE = "indent.rainbow.settings.IrColorsPaletteType"

// Accents in band order, each a dim tint over bg0 of roughly bg_current_word's weight.
private val RAINBOW_ROLES = listOf("orange", "yellow", "green", "aqua", "tan", "purple")
private const val RAINBOW_ALPHA = 0x1A

/** Indent Rainbow's custom palette format: comma-separated AARRGGBB. */
fun indentRainbowPalette(colors: List<Color>, alpha: Int = RAINBOW_ALPHA): String =
    colors.joinToString(", ") { "%02X%06X".format(alpha, it.rgb and 0xFFFFFF) }

fun indentRainbowPalette(variant: Variant): String = indentRainbowPalette(RAINBOW_ROLES.mapNotNull { variant.roles[it] })

/**
 * Points Indent Rainbow's custom palette at the active variant's accents. Registered only when Indent Rainbow is
 * installed (optional dependency); its config is reached by reflection so there is no compile-time dependency, and
 * any mismatch with its API only logs.
 */
class IndentRainbowSync : Disposable {
    private val state get() = GruvboxSettings.getInstance().state

    fun apply(variant: Variant?, enabled: Boolean) {
        if (!enabled || variant == null) return restore()
        safely {
            val config = config()
            if (state.irPaletteType == null) {
                state.irPaletteType = (config.call("getPaletteType") as Enum<*>).name
                state.irCustomPalette = config.call("getCustomPalette") as String
                state.irNumberColors = config.call("getCustomPaletteNumberColors") as Int
            }
            write(config, "CUSTOM", indentRainbowPalette(variant), RAINBOW_ROLES.size)
        }
    }

    fun restore() {
        val type = state.irPaletteType ?: return
        safely { write(config(), type, state.irCustomPalette.orEmpty(), state.irNumberColors) }
        state.irPaletteType = null
        state.irCustomPalette = null
        state.irNumberColors = 0
    }

    override fun dispose() = restore()

    private fun write(config: Any, type: String, palette: String, numberColors: Int) {
        val typeClass = loadClass(PALETTE_TYPE)
        @Suppress("UNCHECKED_CAST")
        val typeValue = java.lang.Enum.valueOf(typeClass as Class<out Enum<*>>, type)
        config.javaClass.getMethod("setPaletteType", typeClass).invoke(config, typeValue)
        config.javaClass.getMethod("setCustomPalette", String::class.java).invoke(config, palette)
        config.javaClass.getMethod("setCustomPaletteNumberColors", Int::class.javaPrimitiveType).invoke(config, numberColors)
        // Same refresh as Indent Rainbow's own settings page.
        val cachedData = loadClass("indent.rainbow.settings.IrCachedData").getField("Companion").get(null)
        cachedData.call("update", config)
        val colors = loadClass("indent.rainbow.IrColors").getField("INSTANCE").get(null)
        colors.call("onSchemeChange")
        colors.call("refreshEditorIndentColors")
    }

    private fun config(): Any = ApplicationManager.getApplication().getService(loadClass("indent.rainbow.settings.IrConfig"))

    private fun loadClass(name: String): Class<*> = Class.forName(name, true, javaClass.classLoader)

    private fun Any.call(name: String, vararg args: Any): Any? =
        javaClass.methods.first { it.name == name && it.parameterCount == args.size }.invoke(this, *args)

    private fun safely(block: () -> Unit) {
        try {
            block()
        } catch (e: Exception) {
            thisLogger().warn("Indent Rainbow sync failed; its API may have changed", e)
        }
    }

    companion object {
        fun getInstance(): IndentRainbowSync? = ApplicationManager.getApplication().getService(IndentRainbowSync::class.java)
    }
}
