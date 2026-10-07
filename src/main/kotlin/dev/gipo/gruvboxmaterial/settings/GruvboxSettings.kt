package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service

enum class TabStyle { UNDERLINE, FILLED }

val ACCENTS = listOf("aqua", "green", "yellow", "orange", "tan", "purple", "red")

class GruvboxState : BaseState() {
    var quietOperators by property(false)
    var dimComments by property(false)
    var softenDocs by property(false)
    var emphasizeDeclarations by property(false)
    var accent by string("aqua")
    var tabStyle by enum(TabStyle.UNDERLINE)
    var indentRainbowSync by property(false)

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

    val readability get() = Readability(quietOperators, dimComments, softenDocs, emphasizeDeclarations)
}

@Service(Service.Level.APP)
@State(name = "GruvboxMaterialSettings", storages = [Storage("gruvbox-material.xml")])
class GruvboxSettings : SimplePersistentStateComponent<GruvboxState>(GruvboxState()) {
    companion object {
        fun getInstance(): GruvboxSettings = service()
    }
}
