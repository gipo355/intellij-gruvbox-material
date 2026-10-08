# Gruvbox Material Islands

A warm, low-glare theme for JetBrains IDEs: the
[gruvbox-material](https://github.com/sainnhe/gruvbox-material) palette
(material foreground) on JetBrains' 2026 Islands layout. Built for long
sessions: no color stands out more than the text, and nothing in the code is
blue.

## Variants

| Theme | Background | Text contrast |
|---|---|---|
| Gruvbox Material Islands (dark soft) | `#32302f` | 7.3:1 |
| Gruvbox Material Islands Medium | `#282828` | 8.2:1 |
| Gruvbox Material Islands Hard | `#1d2021` | 9.1:1 |
| Gruvbox Material Islands Light (soft) | `#f2e5bc` | 6.7:1 |

All four are rendered from one set of palette roles; they differ only in the
colors behind the roles. Each theme selects its own editor scheme.

## Design

- **Warm**: reds, oranges, yellows, greens, aqua and a tan in place of blue.
  Blue survives only in ANSI console output and in icons, where it keeps
  classes and interfaces apart.
- **No bold, no italic**: color does the work. Italic comments and
  parameters are optional settings, off by default.
- **Capped contrast**: no color contrasts more with the background than the
  text does.
- **Dim tints**: search results, diffs and usages get muted backgrounds
  instead of bright blocks. Diff tints are computed so added, deleted,
  modified and conflict blocks sit at the same distance from the background,
  stay apart from each other, and keep the text readable on top.
- **Complete scheme**: every editor key the IDE and its plugins define, in
  scheme files or only in code, is set explicitly, so no stock Darcula or
  IntelliJ color leaks through.
- **Islands layout**: the 2026 JetBrains UI, recolored.

## Install

1. Download the zip from
   [GitHub Releases](https://github.com/gipo355/intellij-gruvbox-material/releases),
   or build it: `./gradlew buildPlugin` (lands in `build/distributions/`).
2. Settings | Plugins | gear icon | Install Plugin from Disk, pick the zip.
3. Settings | Appearance & Behavior | Appearance, select one of the
   **Gruvbox Material Islands** themes.

Works in IntelliJ IDEA, GoLand, WebStorm and DataGrip 2026.2+.

If you imported a **Gruvbox Material Tuned** `.icls` earlier, delete it in
Settings | Editor | Color Scheme to avoid two near-identical schemes.

## Credits

- Palette: [sainnhe/gruvbox-material](https://github.com/sainnhe/gruvbox-material) (MIT).
- Layout: JetBrains Islands.

## License

[MIT](LICENSE)
