"""Generate src/main/resources/themes/GruvboxMaterialIslands.theme.json.

Layout and key set follow JetBrains' Islands Darcula (the template). Color keys that Islands Dark sets and the
template leaves to ExperimentalDark are added, as are parent (ExperimentalDark/Darcula) keys whose color would
otherwise show a cool, bright or black value. Every color is a tools/palette.json name or a palette RGB with alpha.

Usage: IDEA_HOME=<IDE install dir> python3 -I tools/ui/build_theme.py
"""
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JAR = "lib/intellij.platform.ide.impl.jar"
OUT = os.path.join(ROOT, "src/main/resources/themes/GruvboxMaterialIslands.theme.json")
KNOWN = os.path.join(ROOT, "src/test/resources/known-ui-keys.txt")
PALETTE = json.load(open(os.path.join(ROOT, "tools/palette.json")))["colors"]

T = "#00000000"


def a(name, alpha):
    """Palette color with alpha, written as a literal because the colors map holds plain palette names only."""
    return PALETTE[name] + alpha


# Values used by Islands Darcula (its own color names, ExperimentalDark names it borrows, and literals).
TEMPLATE_VALUES = {
    "ForegroundDefault": "fg0",
    "PanelBackground": "bg0",
    "BackgroundDark": "bg0",
    "BackgroundMid": "bg0",
    "BackgroundLight": "bg_dim",
    "BackgroundLightest": "bg3",
    "ToolWindowBackground": "bg0",
    "InputBackground": "bg0",
    "ComboboxBackground": "bg1",
    "BorderLight": "bg1",
    "BorderDark": "bg1",
    "BorderTransparent": T,
    "ComponentBorder": "bg5",
    "ComponentBorderFocus": "aqua",
    "ComponentBorderDisabled": "bg_current_word",
    "PopupBackground": "bg1",
    "PopupBackgroundLight": "bg_current_word",
    "PopupBorder": "bg3",
    "TooltipBackground": "bg1",
    "TooltipBorder": "bg3",
    "HoverBackgroundMid": "bg_current_word",
    "SelectionActive": "bg3",
    "SelectionActiveLight": "bg_current_word",
    "SelectionInactive": "bg_current_word",
    "AltBackgroundLight": "bg1",
    "Gray1.5": "bg1",
    "Gray2": "bg0",
    "Gray3": "bg1",
    "Gray4": "bg_current_word",
    "Gray5": "bg3",
    "Gray6": "bg5",
    "Gray7": "bg5",
    "Gray12": "fg0",
    "#FFFFFF12": "bg_current_word",
    "#FFFFFF16": "bg_current_word",
    "#FFFFFF18": "bg_current_word",
    "#FFFFFF33": "bg3",
    "#868a91": "grey1",
    "#9da0a8": "grey2",
    "#BBBBBB": "fg0",
    "#bbbbbb": "fg0",
    "#ffffff": "fg0",
    "#2D2D2D1A": a("bg_dim", "1A"),
    "#2D2D2D33": a("bg_dim", "33"),
    "#2D2D2D90": a("bg_dim", "90"),
    "#00000000": T,
}

# Islands Dark semantic color names, for the keys it sets that the template does not.
DARK_VALUES = {
    "accent-brand-bg-secondary": "bg_current_word",
    "accent-error-bg": "red",
    "accent-error-bg-secondary": "bg_visual_red",
    "accent-neutral-bg": "bg_current_word",
    "accent-success-bg": "green",
    "accent-success-bg-secondary": "bg_visual_green",
    "control-bg-small": "bg3",
    "control-border-disabled": "bg1",
    "control-border-over-accent": "bg5",
    "control-border-raised": "bg5",
    "control-brand-bg": "aqua",
    "control-brand-border": "aqua",
    "control-success-bg": "bg3",
    "control-success-border": "green",
    "dialog-bg": "bg0",
    "dialog-bg-inline": "bg1",
    "dialog-border": "bg1",
    "editor-bg": "bg0",
    "editor-border": "bg1",
    "feedback-ai-bg": "bg_visual_purple",
    "feedback-ai-border": "bg5",
    "feedback-bg": "bg1",
    "feedback-border": "bg3",
    "feedback-brand-bg": "bg_current_word",
    "feedback-brand-border": "bg5",
    "feedback-control-border": "bg5",
    "feedback-error-bg": "bg_visual_red",
    "feedback-error-border": "search_current",
    "feedback-success-bg": "bg_visual_green",
    "feedback-success-border": "search",
    "feedback-warning-bg": "bg_visual_yellow",
    "feedback-warning-border": "substitute",
    "got-it-bg": "bg_current_word",
    "got-it-code-border": "bg5",
    "got-it-shortcut-bg": "bg_current_word",
    "got-it-text-link": "aqua",
    "got-it-text-step": "grey2",
    "icon-default-stroke": "fg0",
    "icon-green-stroke": "green",
    "icon-over-accent": "fg0",
    "inlay-bg": "bg_current_word",
    "main-window-bg": "bg_dim",
    "popup-bg": "bg1",
    "popup-border": "bg_current_word",
    "popup-completion-match-text": "aqua",
    "presentation-assistant-bg": "bg3",
    "search-match-bg": "search",
    "selection-bg-active": "bg3",
    "selection-bg-hovered": "bg_current_word",
    "tab-bg-hovered": "bg_current_word",
    "tab-file-color-mask-bg": a("bg_dim", "80"),
    "tab-selected-bg-active": "bg3",
    "text-default": "fg0",
    "text-disabled": "grey0",
    "text-error": "red",
    "text-link": "aqua",
    "text-muted": "grey2",
    "text-over-accent": "fg0",
    "text-secondary": "grey1",
    "text-success": "green",
    "text-warning": "yellow",
    "toggle-border": "bg5",
    "toggle-button-bg": "grey2",
    "toggle-off-bg": "bg_dim",
    "tool-window-bg-inline": "bg1",
    "toolbar-bg-hovered": "bg_current_word",
    "toolbar-bg-pressed": "bg3",
    "toolbar-border": "bg_current_word",
    "toolbar-run-bg": "bg_visual_green",
    "toolbar-selected-bg": "bg3",
    "toolbar-selected-bg-active": "bg3",
    "toolbar-selected-bg-hovered": "bg_statusline3",
    "toolbar-stop-bg": "bg_visual_red",
    "tree-indent-guide-border": "bg_current_word",
    "transparent": T,
}

SHADOWS = {
    f"{group}.Shadow.{side}{n}Color": (T if n == 0 else a("bg_dim", alpha))
    for group, alpha in (("Ide", "20"), ("Notification", "10"))
    for side in ("top", "bottom", "left", "right", "topLeft", "topRight", "bottomLeft", "bottomRight")
    for n in (0, 1)
}

# Per-key choices; they win over the value maps above.
KEYS = {
    **SHADOWS,

    # Frame vs islands
    "MainWindow.background": "bg_dim",
    "MainWindow.FullScreeControl.Background": "bg3",
    "MainWindow.Tab.background": "bg_dim",
    "MainWindow.Tab.selectedBackground": "bg0",
    "MainWindow.Tab.separatorColor": "bg1",
    "MainWindow.Tab.hoverForeground": "fg0",
    "MainToolbar.Icon.background": "bg_dim",
    "Plugins.SectionHeader.background": "bg1",
    "WelcomeScreen.Banner.background": "bg1",
    "WelcomeScreen.Projects.actions.background": "bg1",
    "WelcomeScreen.Projects.actions.selectionBackground": "bg3",
    "WelcomeScreen.Projects.actions.selectionBorderColor": "bg5",
    "WelcomeScreen.SidePanel.background": "bg_dim",
    "activeCaption": "bg_dim",
    "SidePanel.background": "bg1",
    "StatusBar.LightEditBackground": "bg1",

    # Popups, tooltips
    "Popup.Header.inactiveBackground": "bg1",
    "CompletionPopup.foreground": "fg0",
    "CompletionPopup.Advertiser.foreground": "grey1",
    "CompletionPopup.selectionBackground": "bg3",
    "ToolTip.foreground": "fg0",
    "Tooltip.foreground": "fg0",
    "Editor.ToolTip.foreground": "fg0",
    "Editor.ToolTip.selectionBackground": "bg3",
    "ParameterInfo.background": "bg1",
    "ParameterInfo.borderColor": "bg3",
    "ParameterInfo.foreground": "fg0",
    "ParameterInfo.currentParameterForeground": "fg0",
    "ParameterInfo.infoForeground": "grey2",
    "FlameGraph.Tooltip.foreground": "fg0",
    "FlameGraph.Tooltip.scaleColor": "bg5",
    "MenuItem.acceleratorForeground": "grey1",
    "AgentPicker.Advertiser.background": "bg1",
    "Debugger.EvaluateExpression.background": "bg1",
    "Toolbar.Floating.background": "bg1",

    # Got It / learning tooltips: a raised warm grey card, not a blue one
    "GotItTooltip.background": "bg3",
    "GotItTooltip.borderColor": "bg5",
    "GotItTooltip.Button.contrastBackground": "bg_current_word",
    "GotItTooltip.animationBackground": "bg3",
    "GotItTooltip.iconBorderColor": "grey2",
    "GotItTooltip.codeForeground": "fg0",
    "GotItTooltip.shortcutForeground": "fg0",
    "Tooltip.Learning.background": "bg3",
    "Tooltip.Learning.borderColor": "bg5",
    "Tooltip.Learning.spanBackground": "bg_current_word",
    "Tooltip.Learning.codeBorderColor": "bg5",
    "Tooltip.Learning.iconFillColor": "bg3",
    "Tooltip.Learning.iconBorderColor": "grey2",
    "Lesson.shortcutBackground": "bg_current_word",
    "Lesson.Badge.newLessonForeground": "fg0",
    "Lesson.stepNumberForeground": "fg0",

    # Notifications, validation
    "Notification.background": "bg1",
    "Notification.borderColor": "bg3",
    "Notification.Button.background": "bg1",
    "Notification.Button.borderColor": "bg5",
    "Notification.MoreButton.background": "bg0",
    "NotificationsToolwindow.newNotification.background": "bg1",
    "UnattendedHostStatus.warningBackground": "bg_visual_yellow",
    "UnattendedHostStatus.warningForeground": "yellow",
    "UnattendedHostStatus.dangerBackground": "bg_visual_red",

    # Buttons, controls
    "Button.default.startBackground": "bg3",
    "Button.default.endBackground": "bg3",
    "Button.default.startBorderColor": "aqua",
    "Button.default.endBorderColor": "aqua",
    "Button.default.focusColor": "aqua",
    "Button.default.focusedBorderColor": "aqua",
    "Button.default.shadowColor": T,
    "Button.disabledText": "grey0",
    "Button.startBackground": "bg1",
    "Button.endBackground": "bg1",
    "Button.startBorderColor": "bg5",
    "Button.endBorderColor": "bg5",
    "Button.focusedBorderColor": "aqua",
    "Button.shadowColor": T,
    "Button.Split.default.separatorColor": "bg5",
    "Component.errorFocusColor": "search_current",
    "Component.inactiveErrorFocusColor": "bg_visual_red",
    "Component.inactiveWarningFocusColor": "bg_visual_yellow",
    "Component.warningFocusColor": "substitute",
    "Component.focusedBorderColor": T,
    "Component.infoForeground": "grey1",
    "ComboBox.ArrowButton.disabledIconColor": "grey0",
    "ComboBox.ArrowButton.iconColor": "grey2",
    "ComboBox.disabledForeground": "grey0",
    "ToggleButton.onBackground": "aqua",
    "ToggleButton.onForeground": "bg0",
    "Plugins.Button.installFillBackground": "bg3",
    "Plugins.Button.updateBackground": "bg3",
    "Plugins.Button.updateBorderColor": "aqua",
    "Plugins.Button.updateForeground": "fg0",
    "Plugins.tagBackground": "bg_current_word",
    "Plugins.paidTagBackground": "bg_current_word",
    "Slider.buttonColor": "grey2",
    "Slider.buttonBorderColor": "bg_dim",
    "Slider.tickColor": "grey1",
    "Slider.trackColor": "bg5",
    "SearchFieldWithExtension.background": "bg_current_word",
    "SegmentedButton.selectedButtonColor": "bg3",
    "ActionButton.hoverBorderColor": T,
    "ActionButton.pressedBorderColor": T,
    "Link.Tag.background": "bg_current_word",
    "Link.Tag.foreground": "grey2",
    "Link.background": "bg1",
    "Link.activeForeground": "aqua",
    "Link.hoverForeground": "aqua",
    "Link.pressedForeground": "orange",
    "Link.visitedForeground": "aqua",
    "Hyperlink.linkColor": "aqua",

    # Progress, counters, badges
    "ProgressBar.progressCounterBackground": "bg3",
    "ProgressBar.progressCounterForeground": "fg0",
    "ProgressBar.indeterminateStartColor": "green",
    "ProgressBar.passedendcolor": "green",
    "ProgressBar.passedEndColor": "green",
    "ProgressBar.failedendcolor": "red",
    "Counter.background": "bg3",
    "Counter.foreground": "fg0",
    "Badge.blueBackground": "bg_current_word",
    "Badge.blueForeground": "aqua",
    "Badge.blueSecondaryBackground": "bg_current_word",
    "Badge.blueSecondaryForeground": "aqua",
    "Badge.greenBackground": "bg_visual_green",
    "Badge.greenForeground": "green",
    "Badge.greenSecondaryBackground": "bg_visual_green",
    "Badge.greenSecondaryForeground": "green",
    "Badge.purpleSecondaryBackground": "bg_visual_purple",
    "Badge.purpleSecondaryForeground": "purple",
    "Badge.graySecondaryBackground": "bg_current_word",
    "Badge.graySecondaryForeground": "grey2",
    "Badge.disabledBackground": "bg1",
    "Badge.disabledForeground": "grey0",
    "MemoryIndicator.allocatedBackground": "bg_current_word",
    "MemoryIndicator.usedBackground": "bg5",
    "Tag.background": "bg3",
    "List.Tag.background": "bg_current_word",
    "List.Tag.foreground": "grey1",
    "Shortcut.borderColor": "bg5",
    "ManagedIdeBadgeBorder": "bg5",
    "ManagedIdeBadgeBackground": "bg3",
    "ManagedIdeBadgeBackgroundHover": "bg_statusline3",
    "ManagedIdeMenuItemHover": "bg_current_word",

    # Tabs, tool windows, drag and drop
    "EditorTabs.underlinedBorderColor": "aqua",
    "EditorTabs.underlinedTabBackground": "bg_current_word",
    "EditorTabs.inactiveUnderlinedTabBorderColor": "bg5",
    "EditorTabs.inactiveUnderlinedTabBackground": "bg1",
    "EditorTabs.hoverBackground": "bg1",
    "EditorTabs.underTabsBorderColor": "bg1",
    "TabbedPane.underlineColor": "aqua",
    "ToolWindow.Stripe.background": "bg_dim",
    "ToolWindow.Stripe.separatorColor": "bg3",
    "ToolWindow.HeaderTab.selectedBackground": "bg_current_word",
    "ToolWindow.Button.DragAndDrop.buttonDropBackground": "bg3",
    "ToolWindow.Button.DragAndDrop.buttonFloatingBackground": "bg3",
    "ToolWindow.DragAndDrop.areaBackground": "bg_current_word",
    "DragAndDrop.borderColor": "aqua",
    "DragAndDrop.areaBorderColor": "aqua",
    "DragAndDrop.rowBackground": "bg3",
    "DragAndDrop.areaBackground": "bg_current_word",
    "TipOfTheDay.Image.borderColor": "bg3",
    "ScreenView.defaultBorderColor": "bg_dim",
    "ScreenView.hoveredBorderColor": "aqua",
    "ScreenView.selectedBorderColor": "aqua",
    "UIDesigner.Placeholder.selectedForeground": "fg0",

    # Search, run widget
    "SpeedSearch.background": "bg1",
    "SpeedSearch.borderColor": "bg3",
    "SearchEverywhere.Advertiser.background": "bg1",
    "RunWidget.foreground": "fg0",
    "RunWidget.hoverBackground": "bg_current_word",
    "RunWidget.pressedBackground": "bg3",

    # Bookmarks
    "Bookmark.MnemonicAvailable.borderColor": "bg5",
    "Bookmark.MnemonicAssigned.background": "bg_visual_yellow",
    "Bookmark.MnemonicAssigned.foreground": "fg0",
    "Bookmark.MnemonicCurrent.background": "bg3",
    "BookmarkMnemonicCurrent.background": "bg3",
    "BookmarkMnemonicCurrent.borderColor": "bg5",
    "BookmarkMnemonicCurrent.foreground": "fg0",

    # Debugger, profiler, charts
    "Debugger.Variables.valueForeground": "tan",
    "Debugger.Variables.collectingDataForeground": "grey1",
    "Debugger.Variables.evaluatingExpressionForeground": "grey1",
    "Debugger.Variables.typeForeground": "grey1",
    "Debugger.Variables.changedValueForeground": "yellow",
    "Debugger.Variables.modifyingValueForeground": "yellow",
    "Profiler.ChartSlider.lineColor": "bg3",
    "Profiler.CpuChart.background": "bg_visual_green",
    "Profiler.CpuChart.borderColor": "green",
    "Profiler.CpuChart.inactiveBackground": "diff_add",
    "Profiler.CpuChart.inactiveBorderColor": "bg_visual_green",
    "Profiler.CpuChart.pointBackground": "green",
    "Profiler.CpuChart.pointBorderColor": "bg0",
    "Profiler.MemoryChart.background": "bg_visual_yellow",
    "Profiler.MemoryChart.borderColor": "tan",
    "Profiler.MemoryChart.inactiveBackground": "diff_change",
    "Profiler.MemoryChart.inactiveBorderColor": "bg_visual_yellow",
    "Profiler.MemoryChart.pointBackground": "tan",
    "Profiler.MemoryChart.pointBorderColor": "bg0",
    "Profiler.Timer.disabledForeground": "grey0",
    "Profiler.LiveChart.horizontalAxisColor": "bg_current_word",
    "LineProfiler.Line.labelBackground": "bg_current_word",
    "LineProfiler.Line.foreground": "grey2",
    "LineProfiler.Line.hoverBackground": "bg3",
    "LineProfiler.HotLine.labelBackground": "bg_visual_red",
    "LineProfiler.HotLine.foreground": "red",
    "LineProfiler.HotLine.hoverBackground": "search_current",
    "LineProfiler.IgnoredLine.labelBackground": "bg_current_word",
    "LineProfiler.IgnoredLine.foreground": "grey0",
    "CompilationCharts.memory.background": "bg_visual_yellow",
    "CompilationCharts.memory.stroke": "yellow",
    "CompilationCharts.cpu.background": "bg_visual_green",
    "CompilationCharts.production.enabled": "bg_visual_green",
    "CompilationCharts.production.disabled": "bg_current_word",
    "CompilationCharts.production.selected": "green",
    "CompilationCharts.production.stroke": "green",
    "DataSummary.Chart.barColor": "aqua",
    "OpenTelemetry.Span.regularBounds": "grey2",
    "OpenTelemetry.Span.regularFillStart": "bg_visual_yellow",
    "OpenTelemetry.Span.regularFillEnd": "bg_visual_red",
    "OpenTelemetry.Span.selectedBounds": "fg0",
    "OpenTelemetry.Span.selectedFillStart": "substitute",
    "OpenTelemetry.Span.selectedFillEnd": "search_current",

    # VCS, review, diff
    "VersionControl.MarkerPopup.borderColor": "bg3",
    "VersionControl.Log.Commit.Reference.foreground": "grey1",
    "VersionControl.Merge.Status.NoConflicts.foreground": "green",
    "VersionControl.Log.Commit.currentBranchBackground": "bg1",
    "VersionControl.Log.Commit.unmatchedForeground": "grey0",
    "VersionControl.Log.Commit.hoveredBackground": "bg_current_word",
    "VersionControl.FileHistory.Commit.selectedBranchBackground": "bg1",
    "VersionControl.GitLog.headIconColor": "yellow",
    "VersionControl.GitLog.localBranchIconColor": "green",
    "VersionControl.GitLog.otherIconColor": "grey1",
    "VersionControl.GitLog.remoteBranchIconColor": "purple",
    "VersionControl.GitLog.tagIconColor": "grey1",
    "VersionControl.HgLog.bookmarkIconColor": "purple",
    "VersionControl.HgLog.headIconColor": "red",
    "VersionControl.HgLog.localTagIconColor": "aqua",
    "VersionControl.HgLog.mqTagIconColor": "tan",
    "VersionControl.HgLog.tipIconColor": "yellow",
    "Review.Branch.Background": "bg1",
    "Review.Branch.Background.Hover": "bg_current_word",
    "Review.State.Background": "bg_current_word",
    "Review.State.Foreground": "grey1",
    "Review.ChatItem.Hover": "bg_current_word",
    "Space.Review.waitForResponseOutline": "yellow",
    "CombinedDiff.BlockBorder.selectedActiveColor": "aqua",

    # File colors (project view / tabs backgrounds)
    "FileColor.Yellow": "bg_visual_yellow",
    "FileColor.Green": "bg_visual_green",
    "FileColor.Orange": "write_usage",
    "FileColor.Rose": "bg_visual_red",
    "FileColor.Violet": "bg_visual_purple",
    "FileColor.Blue": "bg_visual_blue",
    "FileColor.Gray": "bg_current_word",

    # Code With Me
    "CodeWithMe.Users.1.Background": "green",
    "CodeWithMe.Users.2.Background": "red",
    "CodeWithMe.Users.3.Background": "purple",
    "CodeWithMe.Users.4.Background": "orange",
    "CodeWithMe.Users.5.Background": "aqua",
    "CodeWithMe.Users.6.Background": "yellow",
    **{f"CodeWithMe.Users.{n}.{k}": "bg0" for n in range(1, 7)
       for k in ("Foreground", "FollowingBorderTextForeground", "StopFollowingLinkForeground")},
    "CodeWithMe.Buttons.LinkCopied.Background": "bg_visual_green",
    "CodeWithMe.Buttons.RedButton.Background": "bg1",
    "CodeWithMe.Buttons.RedButton.Hovered.Background": "bg_visual_red",
    "CodeWithMe.Buttons.RedButton.Hovered.Foreground": "fg0",
    "CodeWithMe.EndSessionPopup.Background": "bg1",
    "CodeWithMe.EndSessionPopup.EndButton.Background": "bg3",
    "CodeWithMe.EndSessionPopup.EndButton.Foreground": "fg0",
    "CodeWithMe.EndSessionPopup.Foreground": "fg0",
    "CodeWithMe.EndSessionPopup.link": "aqua",
    "CodeWithMe.EndSessionPopup.timer.Foreground": "fg0",

    # Trial widget
    "TrialWidget.Default.background": "bg1",
    "TrialWidget.Default.borderColor": "grey0",
    "TrialWidget.Default.foreground": "fg0",
    "TrialWidget.Default.hoverBackground": "bg_current_word",
    "TrialWidget.Default.hoverBorderColor": "grey1",
    "TrialWidget.Default.hoverForeground": "fg0",
    "TrialWidget.Active.background": "bg_visual_green",
    "TrialWidget.Active.borderColor": "green",
    "TrialWidget.Active.foreground": "green",
    "TrialWidget.Active.hoverBackground": "bg_visual_green",
    "TrialWidget.Active.hoverBorderColor": "green",
    "TrialWidget.Active.hoverForeground": "green",
    "TrialWidget.Alert.background": "bg_visual_yellow",
    "TrialWidget.Alert.borderColor": "yellow",
    "TrialWidget.Alert.foreground": "yellow",
    "TrialWidget.Alert.hoverBackground": "bg_visual_yellow",
    "TrialWidget.Alert.hoverBorderColor": "yellow",
    "TrialWidget.Alert.hoverForeground": "yellow",
    "TrialWidget.Expiring.background": "bg_visual_red",
    "TrialWidget.Expiring.borderColor": "red",
    "TrialWidget.Expiring.foreground": "red",
    "TrialWidget.Expiring.hoverBackground": "bg_visual_red",
    "TrialWidget.Expiring.hoverBorderColor": "red",
    "TrialWidget.Expiring.hoverForeground": "red",
    "TrialWidget.Progress.background": "bg1",
    "TrialWidget.Progress.borderColor": "grey0",
    "TrialWidget.Progress.foreground": "grey1",
    "TrialWidget.Progress.hoverBackground": "bg_current_word",
    "TrialWidget.Progress.hoverBorderColor": "grey1",
    "TrialWidget.Progress.hoverForeground": "grey2",

    # Package search, help, presentation assistant, misc
    "PackageSearch.SearchResult.background": "bg1",
    "PackageSearch.SearchResult.hoverBackground": "bg_current_word",
    "PackageSearch.SearchResult.PackageTag.background": "bg_current_word",
    "PackageSearch.SearchResult.PackageTag.foreground": "fg0",
    "PackageSearch.SearchResult.PackageTag.hoverBackground": "bg3",
    "PackageSearch.SearchResult.PackageTag.selectedBackground": "bg5",
    "PackageSearch.SearchResult.PackageTag.selectedForeground": "fg0",
    "PackageSearch.PackageTag.background": "bg_current_word",
    "PackageSearch.PackageTag.foreground": "grey2",
    "PackageSearch.PackageTagSelected.background": "bg3",
    "PackageSearch.PackageTagSelected.foreground": "fg0",
    "HelpBrowser.UserMessage.background": "bg3",
    "HelpBrowser.UserMessage.Snippet.MoreLines.foreground": "grey1",
    "HelpBrowser.HelpBrowserMessage.Snippet.MoreLines.foreground": "grey1",
    "HelpBrowser.UserMessage.Snippet.MoreLines.hoverBackground": "bg_current_word",
    "HelpBrowser.HelpBrowserMessage.Snippet.MoreLines.hoverBackground": "bg_current_word",
    "HelpBrowser.titleHighlightForeground": "aqua",
    "HelpBrowser.AiEditor.background": "bg0",
    "PresentationAssistant.Bright.Popup.foreground": "fg0",
    "PresentationAssistant.Bright.keymapLabel": "yellow",
    "PresentationAssistant.Pale.Popup.foreground": "fg0",
    "PresentationAssistant.Pale.Popup.border": "bg3",
    "PresentationAssistant.Pale.PopupBackground": "bg1",
    "PresentationAssistant.Pale.keymapLabel": "grey1",
    "NuGet.section.background": "bg1",
    "NuGet.section.hoverBackground": "bg_current_word",

    # "alt" layout: lighter frame, islands stay bg0
    "alt.MainWindow.background": "bg1",
    "alt.MainToolbar.background": "bg1",
    "alt.ToolWindow.Stripe.background": "bg1",
    "alt.StatusBar.background": "bg1",
    "alt.ToolWindow.Header.inactiveBackground": "bg0",
    "alt.ToolWindow.background": "bg0",
    "alt.Borders.color": "bg_current_word",
    "alt.Borders.ContrastBorderColor": "bg_current_word",
    "alt.ToolWindow.Header.borderColor": "bg_current_word",
    "alt.Island.borderColor": "bg0",

    # Recap
    "Recap.ijnext": "bg_visual_purple",
    "Recap.cardBackground": "bg0",
    "Recap.cardBorderColor": "bg0",
    "Recap.cardHeaderTitle": "fg0",
    "Recap.cardHeaderLinkBackground": "bg1",
    "Recap.cardHeaderSubtitle": "grey2",
    "Recap.cardFooterForeground": "fg0",
    "Recap.chroniclesBackground": "bg1",
    "Recap.chroniclesBorderColor": "bg1",
    "Recap.chroniclesBackgroundHovered": "bg3",
    "Recap.chroniclesForeground": "fg0",
    "Recap.chroniclesForegroundGreyed": "grey1",
    "Recap.errorBackground": "bg_visual_yellow",
    "Recap.errorBorder": "substitute",
    "Recap.errorForeground": "fg0",

    # Wildcards only Darcula/ExperimentalDark set
    "*.caretForeground": "fg0",
    "*.selectionBackgroundInactive": "bg_current_word",
    "*.selectionForegroundInactive": "fg0",
    "*.textBackground": "bg0",
    "*.textForeground": "fg0",

    # Set by no parent theme, only by other installed themes; covered in case the IDE's built-in default is blue
    "IconBadge.errorBackground": "red",
    "IconBadge.warningBackground": "yellow",
    "IconBadge.successBackground": "green",
    "IconBadge.infoBackground": "tan",
    "IconBadge.newUiBackground": "aqua",
    "Review.AI.Background": "bg_visual_purple",
    "Review.MetaInfo.StatusLine.Blue": "tan",
    "Review.MetaInfo.StatusLine.Gray": "grey1",
    "Review.Notification.Blue": "tan",
    "Review.Avatar.Border.Status.Accepted": "green",
    "Review.Avatar.Border.Status.NeedReview": "yellow",
    "Review.Avatar.Border.Status.WaitForUpdates": "grey1",
    "Review.Reaction.Background": "bg_current_word",
    "Review.Reaction.Background.Hovered": "bg3",
    "Review.Reaction.Background.Pressed": "bg3",
    "Review.Reaction.Border.Reacted": "aqua",
    "Review.ChatItem.BubblePanel.Border": "bg3",
    "Review.LineFrame.BorderColor": "bg5",
    "Review.Timeline.Thread.Diff.AnchorLine": "diff_text",
    "ReviewList.state.background": "bg_current_word",
    "ReviewList.state.foreground": "grey2",
    "Space.Review.diffAnchorBackground": "diff_text",
    "Space.Review.workingOutline": "aqua",
    "HelpBrowser.AiEditor.verticalMarkerColor": "purple",
    "VersionControl.FileHistory.Diff.addedColor": "green",
    "VersionControl.FileHistory.Diff.deletedColor": "red",
    "VersionControl.FileHistory.Diff.modifiedColor": "tan",
    "ToolWindow.HeaderTab.underlineColor": "aqua",
    "ToolWindow.HeaderTab.inactiveUnderlineColor": "bg5",
    "ToolWindow.HeaderTab.underlinedTabBackground": "bg_current_word",
    "ProgressBar.failedColor": "red",
    "ProgressBar.failedEndColor": "red",
    "CompletionPopup.background": "bg1",
    "CompletionPopup.matchSelectionForeground": "aqua",
    "CompletionPopup.matchSelectedForeground": "aqua",
    "Notification.Link.foreground": "aqua",
    "Notification.errorBackground": "bg_visual_red",
    "Notification.errorBorderColor": "search_current",
    "Notification.errorForeground": "fg0",
    "Notification.ToolWindow.infoBackground": "bg_current_word",
    "Notification.ToolWindow.infoBorderColor": "bg5",
    "Notification.ToolWindow.infoForeground": "fg0",
    "Notification.ToolWindowError.background": "bg_visual_red",
    "Notification.ToolWindowError.foreground": "fg0",
    "Notification.ToolWindowInfo.background": "bg_current_word",
    "Notification.ToolWindowInfo.borderColor": "bg5",
    "Notification.ToolWindowInfo.foreground": "fg0",
    "Notification.ToolWindowWarning.background": "bg_visual_yellow",
    "Notification.ToolWindowWarning.foreground": "fg0",
    "Banner.foreground": "fg0",
    "Banner.errorForeground": "fg0",
    "Banner.warningForeground": "fg0",
    "Banner.informativeBackground": "bg_current_word",
    "Banner.informativeBorderColor": "bg5",
    "Banner.informativeForeground": "fg0",
    "ToolTip.linkForeground": "aqua",
    "GotItTooltip.shortcutBorderColor": "bg5",
    "Table.dropLineColor": "aqua",
    "Table.dropLineShortColor": "aqua",
    "MainToolbar.hoverBackground": "bg_current_word",
    "MainToolbar.pressedBackground": "bg3",
    "Plugins.selectionBackground": "bg3",
    "Plugins.selectionForeground": "fg0",
    "Plugins.lightSelectionBackground": "bg_current_word",
    "Plugins.Button.installFocusedBackground": "bg_current_word",
    "Plugins.Tab.selectedBackground": "bg3",
    "Plugins.Tab.selectedForeground": "fg0",
    "Plugins.Tab.hoverBackground": "bg_current_word",
    "WelcomeScreen.Projects.selectionBackground": "bg3",
    "WelcomeScreen.Projects.selectionInactiveBackground": "bg_current_word",

    # Template literals
    "ToolWindow.Header.borderColor": "bg1",
    "Label.infoForeground": "grey1",
    "EditorTabs.background": "bg0",
    "Notification.Button.foreground": "fg0",
    "Notification.foreground": "fg0",

    # Darcula-era keys the parents still fill with neutral or cool greys
    "control": "bg0",
    "controlText": "fg0",
    "inactiveCaption": "bg_dim",
    "infoText": "fg0",
    "text": "fg0",
    "textText": "fg0",
    "textInactiveText": "grey1",
    "window": "bg0",
    "Content.background": "bg0",
    "DefaultTabs.background": "bg0",
    "Editor.background": "bg0",
    "Editor.foreground": "fg0",
    "EditorPane.inactiveForeground": "fg0",
    "Label.foreground": "fg0",
    "Label.selectedForeground": "fg0",
    "Label.disabledForeground.os.windows": "grey0",
    "OptionPane.messageForeground": "fg0",
    "TitledBorder.titleColor": "fg0",
    "Group.separatorColor": "bg1",
    "SplitPane.highlight": "bg1",
    "ScrollBar.background": "bg0",
    "Spinner.background": "bg0",
    "Tree.background": "bg0",
    "Tree.foreground": "fg0",
    "Table.background": "bg0",
    "Table.foreground": "fg0",
    "TableHeader.background": "bg1",
    "TextArea.background": "bg0",
    "TextArea.selectionForeground": "fg0",
    "TextField.disabledBackground": "bg0",
    "FormattedTextField.background": "bg0",
    "PasswordField.background": "bg0",
    "ComboBoxButton.background": "bg1",
    "TabbedPane.disabledForeground": "grey0",
    "TabbedPane.disabledUnderlineColor": "bg5",
    "RadioButton.darcula.selectionEnabledColor": "aqua",
    "RadioButton.darcula.selectionEnabledShadowColor": "bg_dim",
    "RadioButton.darcula.selectionDisabledColor": "grey0",
    "RadioButton.darcula.selectionDisabledShadowColor": "bg_dim",
    "MainMenu.background": "bg1",
    "MainMenu.foreground": "fg0",
    "MenuBar.borderColor": "bg1",
    "MenuBar.disabledBackground": "bg1",
    "MenuItem.acceleratorSelectionForeground": "fg0",
    "MenuItem.disabledForeground": "grey0",
    "PopupMenu.translucentBackground": "bg1",
    "Popup.Toolbar.borderColor": "bg_current_word",
    "Tooltip.background": "bg1",
    "Tooltip.Actions.background": "bg1",
    "Canvas.Tooltip.background": "bg1",
    "MainToolbar.foreground": "fg0",
    "MainToolbar.Dropdown.background": "bg_dim",
    "MainToolbar.Dropdown.hoverBackground": "bg_current_word",
    "MainToolbar.Icon.hoverBackground": "bg_current_word",
    "MainWindow.Tab.borderColor": "bg_dim",
    "MainWindow.Tab.selectedInactiveBackground": "bg0",
    "StatusBar.hoverBackground": "bg_current_word",
    "ToolWindow.Button.DragAndDrop.stripeBackground": "bg_dim",
    "ToolWindow.HeaderCloseButton.background": "bg_current_word",
    "ToolWindow.HeaderTab.selectedInactiveBackground": "bg1",
    "CompletionPopup.selectionInactiveBackground": "bg_current_word",
    "SearchEverywhere.Header.background": "bg1",
    "SearchEverywhere.List.separatorColor": "bg_current_word",
    "SearchEverywhere.SearchField.background": "bg1",
    "SearchEverywhere.SearchField.borderColor": "bg3",
    "SearchEverywhere.SearchField.infoForeground": "grey1",
    "SpeedSearch.foreground": "fg0",
    "DragAndDrop.areaForeground": "fg0",
    "DisclosureButton.defaultBackground": "bg1",
    "DisclosureButton.hoverOverlay": a("fg0", "0D"),
    "DisclosureButton.pressedOverlay": a("fg0", "1A"),
    "WelcomeScreen.Frame.DisclosureButton.hoverOverlay": a("fg0", "0D"),
    "WelcomeScreen.Frame.DisclosureButton.pressedOverlay": a("fg0", "1A"),
    "WelcomeScreen.background": "bg0",
    "Plugins.background": "bg0",
    "Plugins.borderColor": "bg1",
    "Plugins.SearchField.background": "bg0",
    "Plugins.SectionHeader.foreground": "grey2",
    "PackageSearch.PackageTag.hoverBackground": "bg3",
    "PackageSearch.PackageTag.selectedBackground": "bg3",
    "PackageSearch.PackageTag.selectedForeground": "fg0",
    "ProgressBar.foreground": "aqua",
    "ProgressBar.indeterminateEndColor": "aqua",
    "ProgressBar.passedColor": "green",
    "Lesson.Badge.newLessonBackground": "bg_visual_green",
    "LicenseDialog.freeBadgeBackground": "bg_visual_green",
    "LicenseDialog.freeBadgeForeground": "green",
    "BookmarkMnemonicAssigned.background": "bg_visual_yellow",
    "BookmarkMnemonicAssigned.borderColor": "substitute",
    "Bookmark.iconBackground": "tan",
    "Bookmark.Mnemonic.iconBackground": "bg_visual_yellow",
    "Bookmark.Mnemonic.iconBorderColor": "yellow",
    "CodeWithMe.Buttons.RedButton.Foreground": "red",
    "Focus.color": "red",
    "VersionControl.HgLog.closedBranchIconColor": "red",
    "WelcomeScreen.Frame.DisclosureButton.defaultBackground": "bg1",
    "BookmarkMnemonicAssigned.foreground": "fg0",
    "BookmarkMnemonicAvailable.background": "bg1",
    "BookmarkMnemonicAvailable.borderColor": "bg5",
    "BookmarkMnemonicAvailable.foreground": "fg0",
    "CodeWithMe.Avatar.foreground": "bg0",
    "CodeWithMe.Buttons.BadgeBackground": "bg3",
    "CodeWithMe.Buttons.LinkCopied.Foreground": "green",
    "CodeWithMe.EndSessionPopup.info.Foreground": "grey2",
    "CodeWithMe.MainToolbar.NoConnectionLabelForeground": "grey1",
    "CombinedDiff.BlockBorder.selectedInactiveColor": "bg5",
    "CompilationCharts.background.default": "bg0",
    "CompilationCharts.background.even": "bg1",
    "CompilationCharts.background.odd": "bg0",
    "CompilationCharts.lineColor": "bg_dim",
    "CompilationCharts.textColor": "grey2",
    "CompilationCharts.cpu.stroke": "green",
    "CompilationCharts.test.enabled": "bg_visual_purple",
    "CompilationCharts.test.disabled": "bg_current_word",
    "CompilationCharts.test.selected": "purple",
    "CompilationCharts.test.stroke": "purple",
    "FlameGraph.Tooltip.scaleBackground": "bg3",
    "Profiler.Timer.background": "bg0",
    "AppInspector.GraphNode.background": "bg3",
    "Space.Review.acceptedOutline": "green",
    "VersionControl.HgLog.branchIconColor": "green",
    "VersionControl.HgLog.tagIconColor": "grey1",
    "VersionControl.RefLabel.foreground": "grey1",
    "UIDesigner.Activity.borderColor": "bg_dim",
    "UIDesigner.Canvas.background": "bg_dim",
    "UIDesigner.ColorPicker.background": "bg1",
    "UIDesigner.ColorPicker.foreground": "grey0",
    "UIDesigner.Component.background": "bg3",
    "UIDesigner.Component.borderColor": "bg_dim",
    "UIDesigner.Component.foreground": "grey1",
    "UIDesigner.Component.hoverBorderColor": "grey2",
    "UIDesigner.Connector.borderColor": "grey1",
    "UIDesigner.Connector.hoverBorderColor": "grey2",
    "UIDesigner.Label.foreground": "fg0",
    "UIDesigner.List.selectionBackground": "bg3",
    "UIDesigner.Panel.background": "bg0",
    "UIDesigner.Placeholder.background": "bg3",
    "UIDesigner.Placeholder.borderColor": "bg1",
    "UIDesigner.Placeholder.foreground": "grey1",
    "UIDesigner.highStroke.foreground": "grey2",
    "UIDesigner.percent.foreground": "grey0",

    # Scrollbars: grey1 thumbs at the template's alphas
    "ScrollBar.hoverThumbBorderColor": a("bg_dim", "8C"),
    "ScrollBar.hoverThumbColor": a("grey1", "8C"),
    "ScrollBar.hoverTrackColor": a("grey1", "00"),
    "ScrollBar.thumbBorderColor": a("bg_dim", "59"),
    "ScrollBar.thumbColor": a("grey1", "59"),
    "ScrollBar.trackColor": a("grey1", "00"),
    "ScrollBar.Transparent.hoverThumbBorderColor": a("bg_dim", "8C"),
    "ScrollBar.Transparent.hoverThumbColor": a("grey1", "8C"),
    "ScrollBar.Transparent.hoverTrackColor": a("grey1", "1A"),
    "ScrollBar.Transparent.thumbBorderColor": a("bg_dim", "00"),
    "ScrollBar.Transparent.thumbColor": a("grey1", "59"),
    "ScrollBar.Transparent.trackColor": a("grey1", "00"),
}

# Recent-project tints: the title-bar gradient start and the avatar, each a dim warm tint.
RECENT = {
    1: ("bg_visual_red", "diff_delete", "write_usage"),
    2: ("bg_visual_yellow", "diff_text", "substitute"),
    3: ("bg_visual_green", "diff_add", "search"),
    4: ("diff_add", "bg_visual_green", "bg_statusline3"),
    5: ("diff_change", "write_usage", "bg_visual_yellow"),
    6: ("bg_visual_purple", "bg_visual_purple", "bg_visual_red"),
    7: ("bg_diff_red", "bg_visual_red", "bg_visual_purple"),
    8: ("diff_text", "bg_statusline3", "bg_visual_green"),
    9: ("bg_diff_green", "search", "diff_add"),
}
for n, (gradient, start, end) in RECENT.items():
    KEYS[f"RecentProject.Color{n}.MainToolbarGradientStart"] = gradient
    KEYS[f"RecentProject.Color{n}.Avatar.Start"] = start
    KEYS[f"RecentProject.Color{n}.Avatar.End"] = end

# Project gradients: (diagonal tint, radial glow) per group, over the bg_dim frame.
GRADIENTS = {
    1: ("diff_delete", "search_current"),
    2: ("diff_change", "substitute"),
    3: ("bg_diff_green", "search"),
    4: ("diff_add", "bg_visual_green"),
    5: ("write_usage", "bg_visual_yellow"),
    6: ("diff_delete", "bg_visual_purple"),
    7: ("bg_diff_red", "bg_visual_red"),
    8: ("diff_text", "diff_text"),
    9: ("diff_add", "bg_statusline3"),
}
for n, (diagonal, radial) in GRADIENTS.items():
    g = f"ProjectGradients.Group{n}"
    KEYS.update({
        f"{g}.DiagonalGradient.Color1": diagonal,
        f"{g}.DiagonalGradient.Color2": "bg_dim",
        f"{g}.DiagonalGradient.Color3": diagonal,
        f"{g}.DiagonalGradient.Color4": "bg_dim",
        f"{g}.RadialGradient.Color1": a(radial, "FF"),
        f"{g}.RadialGradient.Color2": a(radial, "00"),
    })

# expUI SVG source colors -> palette. Source hexes come from a survey of the IDE's *_dark.svg expui icons and the
# expUI checkbox/radio SVGs; #3574F0 is the checked checkbox/radio fill, so it follows the aqua accent.
ICON_HEX = {
    "#CED0D6": "fg0",
    "#DFE1E5": "fg0",
    "#B4B8BF": "grey2",
    "#9DA0A8": "grey2",
    "#868A91": "grey1",
    "#6F737A": "grey0",
    "#5A5D63": "bg5",
    "#43454A": "bg3",
    "#2B2D30": "bg0",
    "#393B40": "bg1",
    "#1E1F22": "bg_dim",
    "#548AF7": PALETTE["blue"],
    "#3574F0": "aqua",
    "#25324D": "bg_visual_blue",
    "#2E436E": "bg_visual_blue",
    "#57965C": "green",
    "#5FAD65": "green",
    "#253627": "bg_visual_green",
    "#375239": "bg_visual_green",
    "#DB5C5C": "red",
    "#402929": "bg_visual_red",
    "#F2C55C": "yellow",
    "#D6AE58": "yellow",
    "#3D3223": "bg_visual_yellow",
    "#E08855": "orange",
    "#C77D55": "orange",
    "#45322B": "write_usage",
    "#614438": "write_usage",
    "#A571E6": "purple",
    "#B589EC": "purple",
    "#955AE0": "purple",
    "#2F2936": "bg_visual_purple",
}
# Darcula's icon recolors for selected rows point at blues; keep selected icons on their own palette hues.
ICONS_ON_SELECTION = {
    "#5e5e5e": "grey2",
    "#6e6e6e": "grey2",
    "#9aa7b0cc": "grey2",
    "#9aa7b099": "grey2",
    "#c75450": "red",
    "#f26522b3": "orange",
    "#f2652299": "orange",
    "#62b54399": "green",
    "#f98b9e99": "purple",
    "#b99bf899": "purple",
    "#f4af3d99": "yellow",
}
CHECKBOX = {
    "Checkbox.Background.Default": "bg0",
    "Checkbox.Border.Default": "bg5",
    "Checkbox.Background.Selected": "bg3",
    "Checkbox.Border.Selected": "aqua",
    "Checkbox.Foreground.Selected": "aqua",
    "Checkbox.Focus.Wide": "aqua",
    "Checkbox.Background.Disabled": "bg1",
    "Checkbox.Border.Disabled": "bg_current_word",
    "Checkbox.Foreground.Disabled": "grey0",
}


def merge_pairs(pairs):
    out = {}
    for key, value in pairs:
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_pairs([*out[key].items(), *value.items()])
        else:
            out[key] = value
    return out


def flatten(node, prefix=""):
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, path)
        else:
            yield path, value


def luminance(hex_color):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def off_palette(hex_color):
    """True when a parent color is visible and not a palette color."""
    if len(hex_color) == 9 and hex_color[7:].lower() == "00":
        return False
    return hex_color[:7].lower() not in {v.lower() for v in PALETTE.values()}


def is_color(value):
    return isinstance(value, str) and value.startswith("#") and len(value) in (7, 9)


def insert(tree, path, value):
    """Add a leaf following the source nesting (path is a list of source segments)."""
    node = tree
    for seg in path[:-1]:
        if seg not in node:
            node[seg] = {}
        elif not isinstance(node[seg], dict):
            raise SystemExit(f"{'.'.join(path)}: would replace leaf {seg}")
        node = node[seg]
    node[path[-1]] = value


def segments(node, prefix=()):
    for key, value in node.items():
        if isinstance(value, dict):
            yield from segments(value, prefix + (key,))
        else:
            yield prefix + (key,), value

def env_dir(name):
    path = os.environ.get(name)
    if not path:
        sys.exit(f"{name} is not set (see the usage line at the top of this script)")
    if not os.path.isdir(path):
        sys.exit(f"{name}={path} is not a directory")
    return path


def main():
    ide_home = env_dir("IDEA_HOME")
    with zipfile.ZipFile(os.path.join(ide_home, JAR)) as zf:
        def load(name):
            return json.loads(zf.read(name).decode("utf-8"), object_pairs_hook=merge_pairs)
        template = load("themes/islands/ManyIslandsDarcula.theme.json")
        dark = load("themes/islands/ManyIslandsDark.theme.json")
        exp = load("themes/expUI/expUI_dark.theme.json")
        base = load("themes/darcula.theme.json")

    missing = []
    source = {}

    def pick(key, value, values):
        if key in KEYS:
            return KEYS[key]
        if isinstance(value, str) and value in values:
            return values[value]
        missing.append(f"{key} = {value}")
        return value

    def map_tree(node, prefix=""):
        out = {}
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                out[key] = map_tree(value, path)
            elif isinstance(value, str) and not re.match(r"-?\d|com\.", value):
                out[key] = pick(path, value, TEMPLATE_VALUES)
                source[path] = "template"
            else:
                out[key] = value
        return out

    ui = map_tree(template["ui"])
    have = {k for k, _ in flatten(ui)}

    dark_colors = dark["colors"]
    for path, value in segments(dark["ui"]):
        key = ".".join(path)
        if key in have or not isinstance(value, str):
            continue
        if not (value.startswith("#") or value in dark_colors):
            continue
        insert(ui, list(path), pick(key, value, DARK_VALUES))
        have.add(key)
        source[key] = "dark"

    # Whatever ExperimentalDark/Darcula still supply in a non-palette color.
    parent = {}
    # Darcula's ui borrows ExperimentalDark color names (e.g. "Gray2"), so resolve both with them.
    for theme, colors in ((base, exp["colors"]), (exp, exp["colors"])):
        for path, value in segments(theme["ui"]):
            while isinstance(value, str) and value in colors:
                value = colors[value]
            parent[".".join(path)] = (path, value)
    for key, (path, value) in sorted(parent.items()):
        if ".os." in key and key.split(".os.")[0] in have:
            continue
        if key in have or not is_color(value) or not off_palette(value):
            continue
        if key in KEYS:
            insert(ui, list(path), KEYS[key])
        else:
            missing.append(f"{key} = {value} (parent)")
        have.add(key)
        source[key] = "parent"

    # Keys no parent theme sets but other installed themes do (IDE defaults unverified): nest under an existing group.
    known = set(open(KNOWN).read().split())
    unused = []
    for key in sorted(set(KEYS) - have):
        if key not in known:
            unused.append(key)
            continue
        node, rest = ui, key.split(".")
        while True:
            group = next((n for n in range(len(rest) - 1, 0, -1)
                          if isinstance(node.get(".".join(rest[:n])), dict)), None)
            if group is None:
                break
            node, rest = node[".".join(rest[:group])], rest[group:]
        node[".".join(rest)] = KEYS[key]
        source[key] = "extra"
    if missing or unused:
        for m in missing:
            print("unmapped:", m, file=sys.stderr)
        for u in unused:
            print("KEYS entry not in known-ui-keys.txt:", u, file=sys.stderr)
        sys.exit(1)

    theme = {
        "name": "Gruvbox Material Islands",
        "dark": True,
        "author": "gipo355",
        "parentTheme": "ExperimentalDark",
        "editorScheme": "/themes/GruvboxMaterialIslands.xml",
        "colors": {k: v for k, v in PALETTE.items() if k != "blue"},
        "ui": ui,
        "icons": {"ColorPalette": {**CHECKBOX, **ICON_HEX}},
        "iconColorsOnSelection": ICONS_ON_SELECTION,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(theme, fh, indent=2)
        fh.write("\n")
    counts = {s: sum(1 for v in source.values() if v == s) for s in ("template", "dark", "parent", "extra")}
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
