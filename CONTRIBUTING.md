# Contributing

## Setup

- JDK 21.
- IntelliJ IDEA 2026.2+, optional. Set `ideaHome=/path/to/ide` in `~/.gradle/gradle.properties`; without
  a local install Gradle downloads IU 2026.2 (about 1.5 GB). Override with
  `-PideaHome=/path/to/ide`.

## Build and test

```bash
./gradlew test          # ThemeLintTest: palette, contrast, key checks
./gradlew buildPlugin   # build/distributions/gruvbox-material-islands-<version>.zip
./gradlew verifyPlugin  # IntelliJ Plugin Verifier
./gradlew runIde        # sandbox IDE with the theme installed
```

`verifyPlugin` must report *Compatible*.

## Changing colors

- `tools/palette.py` defines the palette roles for the four variants (dark
  soft, medium, hard; light soft), the diff tint rules and the keyword color
  table. It writes `tools/palette.json` (the color contract: roles, where blue
  is allowed, the contrast cap) and the runtime `palette.json`.
- Every color in the themes and schemes is a palette role; blue only where
  `restricted` allows it, and nothing contrasts more with the background than
  `fg0` does.
- Everything under `src/main/resources/themes/`, `src/main/resources/gruvbox/`
  and `src/test/resources/` is generated from the local IDE install. Change the
  generator, regenerate in this order, and commit both:

  ```bash
  python3 -I tools/palette.py
  IDEA_HOME=<ide dir> python3 -I tools/ui/build_theme.py
  IDEA_HOME=<ide dir> IDEA_PLUGINS_DIR=<user plugins dir> python3 -I tools/scheme/generate.py
  python3 -I tools/scheme/check_scheme.py && python3 -I tools/ui/check_theme.py
  ```

  A second run must leave every file unchanged.
- Editor keys come from the IDE's schemes, plugin scheme files and keys that
  only code defines (scanned from the jars). A new key that only code defines
  must get a value in `tools/scheme/curated.py`, or generation fails.
- Diff tints are solved, not picked: blocks (added, deleted, modified,
  conflict) sit at the same distance from the background, stay apart from
  each other, and keep text above a set share of the `fg0` contrast.
- `ThemeLintTest` gates it per variant: palette only, contrast cap, no bold or
  italic, every key in `scheme-required-keys.txt` (dark) and
  `scheme-required-keys-light.txt` defined, diff tints within bounds, keyword
  table below `fg0`, every `ui` key listed in `known-ui-keys.txt`.
  A new IDE version can add keys: rerun the generators, and refresh
  `known-ui-keys.txt` with `tools/ui/known_ui_keys.py`.

## Pull requests

- Branch from `main`; CI runs `test`, `buildPlugin` and `verifyPlugin`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org):
  `feat:` bumps the minor version, `fix:` the patch, `feat!:` the major.
  `chore:`, `docs:` and `refactor:` stay out of the changelog.

## Release

release-please keeps a release PR open on `main` with the next version and
`CHANGELOG.md`. Merging it tags `v<version>`, creates the GitHub release, and
the publish workflow attaches the zip to it. Marketplace publishing is off for
now. Do not edit `version` by hand.
