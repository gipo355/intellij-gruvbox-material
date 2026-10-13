package dev.gipo.gruvboxmaterial.settings

const val FIXTURE_PALETTE = """
{
  "variants": {
    "variant-dark": {
      "name": "Fixture Dark",
      "dark": true,
      "family": "material",
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
        "bg5": "#5a524c",
        "tint": "#25242380"
      },
      "keywords": {
        "brightness": ["Bright", "Mid"],
        "strength": ["Vivid", "Muted", "Soft"],
        "families": {
          "orange": {"label": "Orange", "colors": [["#da8d53", "#d79c73", "#d0a385"], ["#cf8449", "#cd936a", "#c69a7c"]]}
        }
      },
      "defaultForeground": "material",
      "foregroundLevels": [{"id": "material", "label": "Material"}, {"id": "original", "label": "Original"}],
      "foregrounds": {
        "material": {
          "roles": {"fg0": "#d4be98", "grey1": "#928374", "grey2": "#a89984", "aqua": "#89b482", "orange": "#e78a4e", "tan": "#c4a67e"},
          "keywords": {
            "brightness": ["Bright", "Mid"],
            "strength": ["Vivid", "Muted", "Soft"],
            "families": {
              "orange": {"label": "Orange", "colors": [["#da8d53", "#d79c73", "#d0a385"], ["#cf8449", "#cd936a", "#c69a7c"]]}
            }
          }
        },
        "original": {
          "roles": {"fg0": "#ebdbb2", "grey1": "#9d8f7f", "grey2": "#bdae93", "aqua": "#8ec07c", "orange": "#e78a4e", "tan": "#c4a67e"},
          "keywords": {
            "brightness": ["Bright", "Mid"],
            "strength": ["Vivid", "Muted", "Soft"],
            "families": {
              "orange": {"label": "Orange", "colors": [["#f09a5a", "#e3a77c", "#dbb091"], ["#e5904f", "#d99f73", "#d1a686"]]}
            }
          }
        }
      }
    },
    "variant-light": {
      "name": "Fixture Light",
      "dark": false,
      "family": "material",
      "editorScheme": "Fixture Light Scheme",
      "roles": {"fg0": "#654735", "aqua": "#4c7a5d"},
      "defaultForeground": "mix",
      "foregroundLevels": [{"id": "mix", "label": "Mix"}, {"id": "material", "label": "Material"}],
      "foregrounds": {
        "mix": {"roles": {"fg0": "#654735", "aqua": "#4c7a5d"}},
        "material": {"roles": {"fg0": "#4f3829", "aqua": "#3c6a4d"}}
      }
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
  "parameters": ["DEFAULT_PARAMETER", "DEFAULT_REASSIGNED_PARAMETER"],
  "reassigned": ["DEFAULT_REASSIGNED_LOCAL_VARIABLE", "DEFAULT_REASSIGNED_PARAMETER"],
  "annotations": ["ANNOTATION_NAME_ATTRIBUTES", "DEFAULT_METADATA"],
  "accentUiKeys": {"material-dark": ["Component.focusColor", "*.underlineColor"]},
  "schemeForegroundRoles": {
    "material-dark": {
      "colors": {"CARET_COLOR": "fg0", "LINE_NUMBERS_COLOR": "grey1"},
      "attributes": {
        "DEFAULT_PARAMETER": {"FOREGROUND": "fg0"},
        "DEFAULT_LINE_COMMENT": {"FOREGROUND": "grey2"},
        "DEFAULT_BLOCK_COMMENT": {"FOREGROUND": "grey2"},
        "DEFAULT_DOC_MARKUP": {"FOREGROUND": "tan", "EFFECT_COLOR": "aqua"},
        "DEFAULT_OPERATION_SIGN": {"FOREGROUND": "orange"},
        "DEFAULT_FUNCTION_CALL": {"FOREGROUND": "fg0"}
      }
    }
  },
  "uiForegroundKeys": {"material-dark": {"fg0": ["Label.foreground"], "aqua": ["Component.focusColor", "*.underlineColor"]}},
  "highUiContrast": {"material-dark": {"LINE_NUMBERS_COLOR": {"from": "grey1", "to": "grey2"}, "INDENT_GUIDE": {"from": "bg3", "to": "bg5"}}}
}
"""
