# CLAUDE.md

Theme-only IntelliJ plugin "Gruvbox Material Islands" (id `dev.gipo.gruvboxmaterial`).
Low-glare gruvbox-material themes on the 2026 Islands UI, in four variants:
dark soft, medium, hard and light soft. Per variant: `themes/<stem>.theme.json`
(UI) and `themes/<stem>.xml` (editor scheme; dark parent `Darcula`, light parent
`Default`). `src/main/resources/gruvbox/palette.json` and `groups.json` ship
variant roles, the keyword color table and key groups as data; nothing in this
repo reads them.

## Build

- `./gradlew test` (ThemeLintTest, plain JUnit, no IDE), `./gradlew buildPlugin`,
  `./gradlew verifyPlugin` (must stay "Compatible").
- Compiles against the local IDE from `ideaHome` in `~/.gradle/gradle.properties`,
  IU 262 (2026.2). IntelliJ Platform Gradle Plugin 2.18.1, Kotlin 2.3 (tests
  only), JDK 21.
- The plugin is installed from the zip. Themes are dynamic `themeProvider`s:
  no restart needed.
- Commits on main use Conventional Commits; release-please turns them into
  the version bump, CHANGELOG.md and the GitHub release. Never edit
  `version` by hand. Marketplace publishing is off.

## Generators

Every file under `src/main/resources/themes/`, `src/main/resources/gruvbox/`
and `src/test/resources/` is generated. Fix the generator, never the output;
re-runs must be byte-identical. Order:

1. `python3 -I tools/palette.py`: roles per variant -> `tools/palette.json`
   and the runtime `palette.json`. The diff design rules and the keyword
   table live here.
2. `IDEA_HOME=... python3 -I tools/ui/build_theme.py`: the four theme.json.
3. `IDEA_HOME=... IDEA_PLUGINS_DIR=... python3 -I tools/scheme/generate.py`:
   the four schemes, both required-key lists, `groups.json`.
   `--refresh-nvim` (with `NVIM_CONFIG`) re-dumps gruvbox-material's nvim
   highlights for the alignment report.
4. `IDEA_HOME=... IDEA_PLUGINS_DIR=... python3 -I tools/ui/known_ui_keys.py > src/test/resources/known-ui-keys.txt`
   when the IDE or plugins change.

Checks: `tools/scheme/check_scheme.py`, `tools/ui/check_theme.py`.

## Rules

- `tools/palette.json` is the color contract: roles, where blue is allowed,
  the contrast cap (nothing contrasts more with bg0 than fg0), diff bounds.
- Scheme values are role names in `tools/scheme/curated.py` or mapped from
  the IDE's own schemes; each family resolves once (against dark soft or light
  soft) and every variant renders the same roles.
- Required keys come from Darcula/Default, Islands Dark or expUI Light, plugin
  scheme files and keys only code defines (`tools/scheme/codekeys.py` scans the
  jars). A key only code defines must be curated or generation fails.
- `ThemeLintTest` is the gate: palette only, no blue outside `restricted`,
  contrast cap, no FONT_TYPE, required keys present, diff tints within bounds,
  keyword table below fg0, no unknown `ui` keys.
- No machine paths, usernames or emails in repo files: pass directories via
  the env vars or flags above.
