package dev.gipo.gruvboxmaterial.settings

const val FIXTURE_PALETTE = """
{
  "variants": {
    "variant-dark": {
      "name": "Fixture Dark",
      "dark": true,
      "editorScheme": "Fixture Dark Scheme",
      "roles": {
        "fg0": "#d4be98",
        "grey1": "#928374",
        "grey2": "#a89984",
        "aqua": "#89b482",
        "green": "#a9b665",
        "yellow": "#d8a657",
        "orange": "#e78a4e",
        "tan": "#c4a67e",
        "purple": "#d3869b",
        "red": "#ea6962",
        "bg0": "#32302f",
        "bg3": "#504945",
        "bg_current_word": "#45403d",
        "tint": "#25242380"
      },
      "keywords": {
        "brightness": ["Bright", "Mid"],
        "strength": ["Vivid", "Muted", "Soft"],
        "families": {
          "orange": {"label": "Orange", "colors": [["#da8d53", "#d79c73", "#d0a385"], ["#cf8449", "#cd936a", "#c69a7c"]]}
        }
      }
    },
    "variant-light": {
      "name": "Fixture Light",
      "dark": false,
      "editorScheme": "Fixture Light Scheme",
      "roles": {"fg0": "#654735", "aqua": "#4c7a5d"}
    }
  }
}
"""

const val FIXTURE_GROUPS = """
{
  "operators": ["DEFAULT_OPERATION_SIGN"],
  "comments": ["DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT"],
  "docs": ["DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_MARKUP"],
  "calls": ["DEFAULT_FUNCTION_CALL"],
  "keywords": ["DEFAULT_KEYWORD"],
  "accentUiKeys": ["Component.focusColor", "*.underlineColor"]
}
"""
