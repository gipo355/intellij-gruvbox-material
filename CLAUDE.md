# CLAUDE.md

Theme-only IntelliJ plugin "Gruvbox Material Islands" (id `dev.gipo.gruvboxmaterial`).
Low-halation gruvbox-material dark theme on the 2026 Islands UI. No code, only
resources: `themes/GruvboxMaterialIslands.theme.json` (UI, parent
`ExperimentalDark`) and `themes/GruvboxMaterialIslands.xml` (editor scheme,
parent `Darcula`).

## Build

- `./gradlew test` (ThemeLintTest, plain JUnit, no IDE), `./gradlew buildPlugin`,
  `./gradlew verifyPlugin` (must stay "Compatible").
- Compiles against the local IDE from `ideaHome` in `~/.gradle/gradle.properties`,
  IU 262 (2026.2). IntelliJ Platform Gradle Plugin 2.18.1, Kotlin 2.3 (tests
  only), JDK 21.
- The user installs the zip from disk into the real IDE. The theme is a
  dynamic `themeProvider`: no restart needed.
- Commits on main use Conventional Commits; release-please turns them into
  the version bump, CHANGELOG.md and the GitHub release. Never edit
  `version` by hand. Marketplace publishing is off.

## Layout

- `tools/palette.json` is the color contract: palette, where blue is allowed,
  the brightness cap (`fg0`). Do not add colors to the theme without adding
  them here first.
- `tools/` generators regenerate the theme files and the test key lists
  (`src/test/resources/known-ui-keys.txt`, `scheme-required-keys.txt`) from
  the local IDE install. Fix the generator, not the generated file.
- `ThemeLintTest` is the gate: palette only, no blue outside `restricted`,
  nothing brighter than `fg0`, no FONT_TYPE (bold/italic), required scheme
  keys present, no unknown `ui` keys.
