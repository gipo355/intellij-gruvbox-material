# Gruvbox Material Islands

A warm, low-glare dark theme for JetBrains IDEs: the
[gruvbox-material](https://github.com/sainnhe/gruvbox-material) palette
(soft background, material foreground) on JetBrains' 2026 Islands layout.

Built for long sessions and for eyes that see halos around bright text at
night. Nothing on screen is brighter than the foreground, and nothing in the
code is blue.

## Design

- **Warm**: reds, oranges, yellows, greens, aqua and a tan in place of blue.
  Blue survives only in ANSI console output and in icons, where it keeps
  classes and interfaces apart.
- **No bold, no italic**: weight changes bloom; color does the work.
- **Capped brightness**: no color is brighter than the foreground `#d4be98`.
- **Moderate contrast**: about 7:1 for text on `#32302f`. Readable without
  glowing.
- **Dim tints**: search results, diffs and usages get muted backgrounds
  instead of bright blocks.
- **Islands layout**: the 2026 JetBrains UI, recolored.

## Install

1. Download the zip from
   [GitHub Releases](https://github.com/gipo355/intellij-gruvbox-material/releases),
   or build it: `./gradlew buildPlugin` (lands in `build/distributions/`).
2. Settings | Plugins | gear icon | Install Plugin from Disk, pick the zip.
3. Settings | Appearance & Behavior | Appearance, select
   **Gruvbox Material Islands**.

Works in IntelliJ IDEA, GoLand, WebStorm and DataGrip 2026.2+.

If you imported a **Gruvbox Material Tuned** `.icls` earlier, delete it in
Settings | Editor | Color Scheme to avoid two near-identical schemes.

## Credits

- Palette: [sainnhe/gruvbox-material](https://github.com/sainnhe/gruvbox-material) (MIT).
- Layout: JetBrains Islands.

## License

[MIT](LICENSE)
