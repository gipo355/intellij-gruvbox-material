package dev.gipo.gruvboxmaterial.settings

import com.intellij.ide.AppLifecycleListener
import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.application.EDT
import com.intellij.openapi.editor.colors.EditorColorsListener
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class GruvboxListener : LafManagerListener, EditorColorsListener, AppLifecycleListener {
    override fun lookAndFeelChanged(source: LafManager) = GruvboxService.getInstance().applyAll()

    override fun globalSchemeChange(scheme: EditorColorsScheme?) = GruvboxService.getInstance().applyScheme()

    override fun appWillBeClosed(isRestart: Boolean) = GruvboxService.getInstance().restoreScheme()
}

class GruvboxStartup : ProjectActivity {
    override suspend fun execute(project: Project) = withContext(Dispatchers.EDT) { GruvboxService.getInstance().startOnce() }
}
