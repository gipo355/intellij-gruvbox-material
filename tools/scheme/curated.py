"""Hand-curated tables. Every color is a palette name (tools/palette.json), never hex.

Sources of each choice: the user's Neovim (tools/scheme/nvim-highlights.json, gruvbox-material soft/material
with blue remapped to tan and no bold/italic), mapped onto IntelliJ keys by meaning.

nvim group                         -> palette   IntelliJ
Normal                             fg0 / bg0    TEXT
Comment                            grey2        DEFAULT_*_COMMENT, DEFAULT_DOC_COMMENT
@keyword (all kinds)               red          DEFAULT_KEYWORD
@operator, @keyword.operator       orange       DEFAULT_OPERATION_SIGN
@punctuation.bracket               fg0          DEFAULT_BRACES/BRACKETS/PARENTHS
@punctuation.delimiter             grey1        DEFAULT_COMMA/SEMICOLON/DOT
@string / @character               aqua         DEFAULT_STRING
@string.escape / @string.regexp    green        DEFAULT_VALID_STRING_ESCAPE, JS.REGEXP
@number / @boolean                 purple       DEFAULT_NUMBER
@constant                          fg0          DEFAULT_CONSTANT
@constant.builtin, @variable.builtin purple     DEFAULT_PREDEFINED_SYMBOL
@function / .call / .method        green        DEFAULT_FUNCTION_*, DEFAULT_*_METHOD
@type / @type.builtin              yellow       DEFAULT_CLASS_NAME/REFERENCE, DEFAULT_INTERFACE_NAME
@module                            yellow       GO_PACKAGE
@variable / @variable.parameter    fg0          DEFAULT_IDENTIFIER, DEFAULT_*_VARIABLE, DEFAULT_PARAMETER
@variable.member / @property       tan          DEFAULT_INSTANCE_FIELD, DEFAULT_STATIC_FIELD
@attribute / @annotation           purple       DEFAULT_METADATA
@label                             orange       DEFAULT_LABEL
@tag / @tag.attribute / delimiter  orange/green/green  DEFAULT_TAG / DEFAULT_ATTRIBUTE / HTML_TAG
@markup.heading / link / url       orange/aqua/tan     MARKDOWN_HEADER / MARKDOWN_LINK_TEXT / *_HYPERLINK
Todo                               tan (fg only: nvim's solid block is dropped)  TODO_DEFAULT_ATTRIBUTES
DiagnosticError/Warn/Info/Hint     red/yellow/tan/purple  ERRORS / WARNING / WEAK_WARNING / INFO
DiagnosticUnnecessary              grey1        NOT_USED_ELEMENT_ATTRIBUTES
DiagnosticDeprecated               strike fg0   DEPRECATED_ATTRIBUTES
SpellBad / SpellCap                red / tan wave  TYPO / GRAMMAR_ERROR
DiffAdd/Delete/Change/Text         diff_ins/diff_del/diff_mod_line/diff_mod (tools/palette.py)  DIFF_INSERTED/DELETED/MODIFIED
Search / CurSearch                 search / search_current  SEARCH_RESULT_*, terminal search
LspReferenceText / Write           bg_current_word / write_usage  IDENTIFIER_UNDER_CARET / WRITE_*
Visual / CursorLine / MatchParen   bg3 / bg1 / bg3  SELECTION_BACKGROUND / CARET_ROW_COLOR / MATCHED_BRACE
LineNr / CursorLineNr              bg5 (light: grey0) / grey1  LINE_NUMBERS_COLOR / LINE_NUMBER_ON_CARET_ROW_COLOR
Folded                             grey1 on bg1 FOLDED_TEXT_ATTRIBUTES
NonText / Whitespace               bg5          WHITESPACES, SOFT_WRAP_SIGN_COLOR
"""

# EFFECT_TYPE codes as IntelliJ serializes them.
BOX, LINE, WAVE, STRIKE, BOLD_DOTTED = 0, 1, 2, 3, 5


def A(fg=None, bg=None, effect=None, effect_type=None, stripe=None):
    value = {}
    if fg:
        value["FOREGROUND"] = fg
    if bg:
        value["BACKGROUND"] = bg
    if effect:
        value["EFFECT_COLOR"] = effect
    if effect_type is not None:
        value["EFFECT_TYPE"] = str(effect_type)
    if stripe:
        value["ERROR_STRIPE_COLOR"] = stripe
    return {"base": None, "value": value}


def L(base):
    return {"base": base, "value": None}


# Explicitly "no styling": used where Darcula/Default also define nothing visible.
NONE = {"base": None, "value": {}}

# ---------------------------------------------------------------- editor colors (<colors>)
# "" keeps IntelliJ's own meaning of an empty color (e.g. selection keeps syntax foregrounds).
COLORS = {
    "CARET_COLOR": "fg0",
    "CARET_ROW_COLOR": "bg1",
    "SELECTION_BACKGROUND": "bg3",
    "SELECTION_BACKGROUND_INACTIVE": "bg_current_word",
    "SELECTION_FOREGROUND": "",
    "READONLY_FRAGMENT_BACKGROUND": "",
    # Islands: gutter and console share the editor background.
    "GUTTER_BACKGROUND": "bg0",
    "EDITOR_GUTTER_BACKGROUND": "bg0",
    "CONSOLE_BACKGROUND_KEY": "bg0",
    "LINE_NUMBERS_COLOR": "bg5",
    "LINE_NUMBER_ON_CARET_ROW_COLOR": "grey1",
    "INDENT_GUIDE": "bg3",
    "SELECTED_INDENT_GUIDE": "grey0",
    "VISUAL_INDENT_GUIDE": "bg1",
    "MATCHED_BRACES_INDENT_GUIDE_COLOR": "grey0",
    "STRING_CONTENT_INDENT_GUIDE": "bg3",
    "WHITESPACES": "bg5",
    "SOFT_WRAP_SIGN_COLOR": "bg5",
    "RIGHT_MARGIN_COLOR": "bg1",
    "METHOD_SEPARATORS_COLOR": "bg3",
    "TEARLINE_COLOR": "bg3",
    "SELECTED_TEARLINE_COLOR": "bg5",
    "FOLDED_TEXT_BORDER_COLOR": "bg3",
    "DIFF_SEPARATORS_BACKGROUND": "bg1",
    "DIFF_SEPARATOR_WAVE": "bg5",
    "RECENT_LOCATIONS_SELECTION": "bg1",
    "GRID_STRIPE_COLOR": "bg1",
    # Islands: popups and hints sit one step above the editor.
    "DOCUMENTATION_COLOR": "bg1",
    "LOOKUP_COLOR": "bg1",
    "NOTIFICATION_BACKGROUND": "bg1",
    "PROMOTION_PANE": "bg1",
    "INFORMATION_HINT": "bg1",
    "QUESTION_HINT": "bg1",
    "ERROR_HINT": "bg_visual_red",
    "HINT_BORDER": "bg3",
    "DOC_COMMENT_GUIDE": "bg3",
    "DOC_COMMENT_LINK": "aqua",
    "INLINE_REFACTORING_SETTINGS_DEFAULT": "bg1",
    "INLINE_REFACTORING_SETTINGS_FOCUSED": "bg3",
    "INLINE_REFACTORING_SETTINGS_HOVERED": "bg3",
    "MODIFIED_TAB_ICON": "tan",
    "ANNOTATIONS_COLOR": "grey1",
    "ANNOTATIONS_LAST_COMMIT_COLOR": "grey2",
    # VCS blame age, newest -> oldest.
    "VCS_ANNOTATIONS_COLOR_1": "bg_statusline3",
    "VCS_ANNOTATIONS_COLOR_2": "bg3",
    "VCS_ANNOTATIONS_COLOR_3": "bg_current_word",
    "VCS_ANNOTATIONS_COLOR_4": "bg1",
    "VCS_ANNOTATIONS_COLOR_5": "bg_dim",
    # Gutter change markers: the diff hues at full accent (inserted green, modified yellow, deleted red).
    "ADDED_LINES_COLOR": "green",
    "MODIFIED_LINES_COLOR": "yellow",
    "DELETED_LINES_COLOR": "red",
    "IGNORED_ADDED_LINES_BORDER_COLOR": "green",
    "IGNORED_MODIFIED_LINES_BORDER_COLOR": "yellow",
    "IGNORED_DELETED_LINES_BORDER_COLOR": "red",
    "WHITESPACES_MODIFIED_LINES_COLOR": "grey0",
    "REVIEW_CHANGED_LINES_COLOR": "yellow",
    # Next edit suggestions: the insert/delete diff tints.
    "NEXT_EDIT.DIFF_ADD_BACKGROUND": "diff_ins",
    "NEXT_EDIT.DIFF_AFTER_BACKGROUND": "diff_ins_line",
    "NEXT_EDIT.REMOVAL_BACKGROUND": "diff_del",
    # File status (tabs, project tree).
    "FILESTATUS_ADDED": "green",
    "FILESTATUS_COPIED": "green",
    "FILESTATUS_addedOutside": "green",
    "FILESTATUS_MODIFIED": "yellow",
    "FILESTATUS_modifiedOutside": "yellow",
    "FILESTATUS_NOT_CHANGED_IMMEDIATE": "yellow",
    "FILESTATUS_NOT_CHANGED_RECURSIVE": "yellow",
    "FILESTATUS_NOT_CHANGED": "",
    "FILESTATUS_SUPPRESSED": "",
    "FILESTATUS_DELETED": "grey1",
    "FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM": "grey1",
    "FILESTATUS_IDEA_FILESTATUS_IGNORED": "grey0",
    "FILESTATUS_OBSOLETE": "grey0",
    "FILESTATUS_MERGED": "purple",
    "FILESTATUS_RENAMED": "aqua",
    "FILESTATUS_SWITCHED": "aqua",
    "FILESTATUS_HIJACKED": "yellow",
    "FILESTATUS_UNKNOWN": "orange",
    "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS": "red",
    "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS": "red",
    "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS": "red",
    "FILESTATUS_changelistConflict": "red",
    "FILESTATUS_IDEA_SVN_FILESTATUS_EXTERNAL": "green",
    "FILESTATUS_IDEA_SVN_FILESTATUS_OBSTRUCTED": "orange",
    "FILESTATUS_IDEA_SVN_REPLACED": "yellow",
    "FILESTATUS_IGNORE.PROJECT_VIEW.IGNORED": "grey1",
    # Keys only code defines (codekeys.py).
    "WARNING_HINT": "bg_visual_yellow",
    "Tag.background": "bg3",
    "BookmarkIcon.background": "bg_visual_yellow",
    "SCHEMA_DIFF_DELETED_KEY": "red",
    # Image editor checkerboard. The white and the black cell keys share the name IMAGES_WHITE_CELL_COLOR.
    "IMAGES_BACKGROUND": "bg0",
    "IMAGES_WHITE_CELL_COLOR": "bg3",
    "IMAGES_GRID_LINE_COLOR": "bg5",
    "NEXT_EDIT_AGENT_DELEGATION.TASK_STATUS_FOREGROUND": "grey1",
    "NEXT_EDIT_AGENT_DELEGATION.TASK_RANGE_BACKGROUND": "bg_visual_purple",
    "NEXT_EDIT_AGENT_DELEGATION.TASK_RANGE_SHIMMER": "bg5",
    "NEXT_EDIT_AGENT_DELEGATION.TASK_FINISHED_FLASH": "bg_visual_green",
}

# Light variant only, over COLORS: bg5 on the light bg0 is too faint for line numbers.
LIGHT_COLORS = {
    "LINE_NUMBERS_COLOR": "grey0",
}

# ---------------------------------------------------------------- semantic core (DEFAULT_* and editor attributes)
CORE = {
    "TEXT": A(fg="fg0", bg="bg0"),
    "DEFAULT_IDENTIFIER": A(fg="fg0"),
    "DEFAULT_KEYWORD": A(fg="red"),
    "DEFAULT_NUMBER": A(fg="purple"),
    "DEFAULT_STRING": A(fg="aqua"),
    "DEFAULT_VALID_STRING_ESCAPE": A(fg="green"),
    "DEFAULT_INVALID_STRING_ESCAPE": A(fg="aqua", effect="red", effect_type=WAVE),
    "DEFAULT_LINE_COMMENT": A(fg="grey2"),
    "DEFAULT_BLOCK_COMMENT": A(fg="grey2"),
    "DEFAULT_DOC_COMMENT": A(fg="grey2"),
    "DEFAULT_DOC_MARKUP": A(fg="grey2"),
    "DEFAULT_DOC_COMMENT_TAG": A(fg="grey2", effect="grey0", effect_type=LINE),
    "DEFAULT_DOC_COMMENT_TAG_VALUE": A(fg="tan"),
    "DEFAULT_OPERATION_SIGN": A(fg="orange"),
    "DEFAULT_BRACES": A(fg="fg0"),
    "DEFAULT_BRACKETS": A(fg="fg0"),
    "DEFAULT_PARENTHS": A(fg="fg0"),
    "DEFAULT_COMMA": A(fg="grey1"),
    "DEFAULT_SEMICOLON": A(fg="grey1"),
    "DEFAULT_DOT": A(fg="grey1"),
    "DEFAULT_FUNCTION_DECLARATION": A(fg="green"),
    "DEFAULT_FUNCTION_CALL": A(fg="green"),
    "DEFAULT_INSTANCE_METHOD": A(fg="green"),
    "DEFAULT_STATIC_METHOD": A(fg="green"),
    "DEFAULT_CLASS_NAME": A(fg="yellow"),
    "DEFAULT_INTERFACE_NAME": A(fg="yellow"),
    "DEFAULT_CLASS_REFERENCE": A(fg="yellow"),
    "DEFAULT_CONSTANT": A(fg="fg0"),
    "DEFAULT_PREDEFINED_SYMBOL": A(fg="purple"),
    "DEFAULT_LOCAL_VARIABLE": A(fg="fg0"),
    "DEFAULT_GLOBAL_VARIABLE": A(fg="fg0"),
    "DEFAULT_PARAMETER": A(fg="fg0"),
    "DEFAULT_REASSIGNED_LOCAL_VARIABLE": A(effect="grey1", effect_type=LINE),
    "DEFAULT_REASSIGNED_PARAMETER": A(effect="grey1", effect_type=LINE),
    "DEFAULT_HIGHLIGHTED_REFERENCE": A(effect="grey1", effect_type=LINE),
    "DEFAULT_INSTANCE_FIELD": A(fg="tan"),
    "DEFAULT_STATIC_FIELD": A(fg="tan"),
    "DEFAULT_METADATA": A(fg="purple"),
    "DEFAULT_LABEL": A(fg="orange"),
    "DEFAULT_TAG": A(fg="orange"),
    "DEFAULT_ATTRIBUTE": A(fg="green"),
    "DEFAULT_ENTITY": A(fg="aqua"),
    "DEFAULT_TEMPLATE_LANGUAGE_COLOR": A(bg="bg1"),
    # Old-style keys kept in the Default scheme.
    "INSTANCE_FIELD_ATTRIBUTES": L("DEFAULT_INSTANCE_FIELD"),
    "STATIC_FIELD_ATTRIBUTES": L("DEFAULT_STATIC_FIELD"),
    "STATIC_FINAL_FIELD_ATTRIBUTES": L("DEFAULT_CONSTANT"),
    "STATIC_METHOD_ATTRIBUTES": L("DEFAULT_STATIC_METHOD"),
    "CUSTOM_STRING_ATTRIBUTES": L("DEFAULT_STRING"),
    "CUSTOM_NUMBER_ATTRIBUTES": L("DEFAULT_NUMBER"),
    "CUSTOM_VALID_STRING_ESCAPE_ATTRIBUTES": L("DEFAULT_VALID_STRING_ESCAPE"),
    "CUSTOM_INVALID_STRING_ESCAPE_ATTRIBUTES": L("DEFAULT_INVALID_STRING_ESCAPE"),
    "CUSTOM_LINE_COMMENT_ATTRIBUTES": L("DEFAULT_LINE_COMMENT"),
    "CUSTOM_MULTI_LINE_COMMENT_ATTRIBUTES": L("DEFAULT_BLOCK_COMMENT"),
    "CUSTOM_KEYWORD1_ATTRIBUTES": L("DEFAULT_KEYWORD"),
    "CUSTOM_KEYWORD2_ATTRIBUTES": A(fg="purple"),
    "CUSTOM_KEYWORD3_ATTRIBUTES": A(fg="aqua"),
    "CUSTOM_KEYWORD4_ATTRIBUTES": A(fg="yellow"),
    # Editor highlights.
    "MATCHED_BRACE_ATTRIBUTES": A(bg="bg3"),
    "MATCHED_TAG_NAME": A(bg="bg3"),
    "UNMATCHED_BRACE_ATTRIBUTES": A(fg="red", bg="bg_visual_red"),
    "FOLDED_TEXT_ATTRIBUTES": A(fg="grey1", bg="bg1"),
    "SEARCH_RESULT_ATTRIBUTES": A(bg="search", stripe="green"),
    "TEXT_SEARCH_RESULT_ATTRIBUTES": A(bg="search", stripe="green"),
    "WRITE_SEARCH_RESULT_ATTRIBUTES": A(bg="write_usage", stripe="orange"),
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES": A(bg="bg_current_word", stripe="grey1"),
    "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": A(bg="write_usage", stripe="orange"),
    "REGEXP_MATCHED_GROUPS": A(bg="bg_visual_yellow"),
    "BLINKING_HIGHLIGHTS_ATTRIBUTES": A(effect="grey2", effect_type=BOX),
    "LIVE_TEMPLATE_ATTRIBUTES": A(effect="tan", effect_type=BOX),
    "LIVE_TEMPLATE_INACTIVE_SEGMENT": A(effect="grey0", effect_type=BOX),
    "TEMPLATE_VARIABLE_ATTRIBUTES": A(fg="purple"),
    "INJECTED_LANGUAGE_FRAGMENT": NONE,
    "TODO_DEFAULT_ATTRIBUTES": A(fg="tan", stripe="tan"),
    "TODO_ATTRIBUTES": L("TODO_DEFAULT_ATTRIBUTES"),
    "BOOKMARKS_ATTRIBUTES": A(stripe="grey2"),
    # Diagnostics.
    "ERRORS_ATTRIBUTES": A(effect="red", effect_type=WAVE, stripe="red"),
    "WRONG_REFERENCES_ATTRIBUTES": A(fg="red"),
    "BAD_CHARACTER": A(effect="red", effect_type=WAVE),
    "RUNTIME_ERROR": A(effect="red", effect_type=BOLD_DOTTED, stripe="red"),
    "WARNING_ATTRIBUTES": A(effect="yellow", effect_type=WAVE, stripe="yellow"),
    "WEAK_WARNING_ATTRIBUTES": A(effect="tan", effect_type=WAVE, stripe="tan"),
    "INFO_ATTRIBUTES": A(effect="purple", effect_type=WAVE, stripe="purple"),
    "CONSIDERATION_ATTRIBUTES": NONE,
    "INFORMATION_ATTRIBUTES": NONE,
    "GENERIC_SERVER_ERROR_OR_WARNING": A(effect="orange", effect_type=LINE, stripe="orange"),
    "DUPLICATE_FROM_SERVER": A(bg="bg_visual_yellow"),
    "NOT_USED_ELEMENT_ATTRIBUTES": A(fg="grey1", stripe="yellow"),
    "DEPRECATED_ATTRIBUTES": A(effect="fg0", effect_type=STRIKE),
    "MARKED_FOR_REMOVAL_ATTRIBUTES": A(effect="red", effect_type=STRIKE),
    "TYPO": A(effect="red", effect_type=WAVE),
    "GRAMMAR_ERROR": A(effect="tan", effect_type=WAVE),
    "JOIN_POINT": A(effect="grey1", effect_type=LINE),
    # Links.
    "HYPERLINK_ATTRIBUTES": A(fg="tan", effect="tan", effect_type=LINE),
    "FOLLOWED_HYPERLINK_ATTRIBUTES": A(fg="purple", effect="purple", effect_type=LINE),
    "INACTIVE_HYPERLINK_ATTRIBUTES": A(effect="grey1", effect_type=LINE),
    "CTRL_CLICKABLE": A(fg="tan", effect="tan", effect_type=LINE),
    # Inlays (nvim LspInlayHint is bg5; one step up to grey0 so hints stay readable on their bg1 pill).
    "INLAY_DEFAULT": A(fg="grey0", bg="bg1"),
    "INLAY_TEXT_WITHOUT_BACKGROUND": A(fg="grey0"),
    "INLINE_PARAMETER_HINT": A(fg="grey0", bg="bg1"),
    "INLINE_PARAMETER_HINT_HIGHLIGHTED": A(fg="grey2", bg="bg3"),
    "INLINE_PARAMETER_HINT_CURRENT": A(fg="grey2", bg="bg3"),
    "INLAY_BUTTON_DEFAULT": A(fg="grey1", effect="bg3"),
    "INLAY_BUTTON_FOCUSED": A(fg="grey1", effect="bg5"),
    "INLAY_BUTTON_HOVERED": A(fg="grey1", effect="bg5"),
    "INLAY_BUTTON_HINT": A(fg="grey1"),
    "INLINE_SUGGESTION": A(fg="grey0"),
    "CODE_LENS_BORDER_COLOR": A(effect="bg3", effect_type=BOX),
    # Diff. BACKGROUND paints whole blocks and changed words; FOREGROUND is the line under word highlights (set, so
    # the platform never mixes BACKGROUND 60% into the editor background); ERROR_STRIPE_COLOR is the marker.
    "DIFF_INSERTED": A(fg="diff_ins_line", bg="diff_ins", stripe="green"),
    "DIFF_DELETED": A(fg="diff_del_line", bg="diff_del", stripe="red"),
    "DIFF_MODIFIED": A(fg="diff_mod_line", bg="diff_mod", stripe="yellow"),
    "DIFF_CONFLICT": A(fg="diff_conf_line", bg="diff_conf", stripe="purple"),
    "DIFF_UNKNOWN": A(bg="diff_mod_line"),
    "DIFF_ABSENT": A(bg="bg1"),
    "DIFF_DELETED_FROM_FS": A(bg="diff_del_line"),
    "DELETED_TEXT_ATTRIBUTES": A(fg="grey1", bg="diff_del_line", effect="grey1", effect_type=STRIKE),
    # Debugger.
    "BREAKPOINT_ATTRIBUTES": A(bg="bg_visual_red", stripe="red"),
    "EXECUTIONPOINT_ATTRIBUTES": A(bg="bg_visual_yellow"),
    "NOT_TOP_FRAME_ATTRIBUTES": A(bg="bg_visual_blue"),
    "INLINE_STACK_FRAMES": A(bg="bg_visual_purple"),
    "EVALUATED_EXPRESSION_ATTRIBUTES": A(bg="bg_current_word"),
    "EVALUATED_EXPRESSION_EXECUTION_LINE_ATTRIBUTES": A(bg="bg3"),
    "DEBUGGER_INLINED_VALUES": A(fg="grey0"),
    "DEBUGGER_INLINED_VALUES_EXECUTION_LINE": A(fg="grey1"),
    "DEBUGGER_INLINED_VALUES_MODIFIED": A(fg="orange"),
    "LINE_FULL_COVERAGE": A(fg="green"),
    "LINE_PARTIAL_COVERAGE": A(fg="yellow"),
    "LINE_NONE_COVERAGE": A(fg="red"),
    # Console (ANSI blue/cyan may use blue; gruvbox's cyan is aqua).
    "CONSOLE_NORMAL_OUTPUT": A(fg="fg0"),
    "CONSOLE_SYSTEM_OUTPUT": A(fg="grey2"),
    "CONSOLE_ERROR_OUTPUT": A(fg="red"),
    "CONSOLE_USER_INPUT": A(fg="green"),
    "CONSOLE_BLACK_OUTPUT": A(fg="bg5", bg="bg1"),
    "CONSOLE_RED_OUTPUT": A(fg="red", bg="bg_visual_red"),
    "CONSOLE_GREEN_OUTPUT": A(fg="green", bg="bg_visual_green"),
    "CONSOLE_YELLOW_OUTPUT": A(fg="yellow", bg="bg_visual_yellow"),
    "CONSOLE_BLUE_OUTPUT": A(fg="blue", bg="bg_visual_blue"),
    "CONSOLE_MAGENTA_OUTPUT": A(fg="purple", bg="bg_visual_purple"),
    "CONSOLE_CYAN_OUTPUT": A(fg="aqua", bg="bg_visual_blue"),
    "CONSOLE_GRAY_OUTPUT": A(fg="grey1", bg="bg3"),
    "CONSOLE_DARKGRAY_OUTPUT": A(fg="grey0", bg="bg3"),
    "CONSOLE_WHITE_OUTPUT": A(fg="fg0", bg="bg5"),
    "CONSOLE_RED_BRIGHT_OUTPUT": A(fg="red", bg="bg_visual_red"),
    "CONSOLE_GREEN_BRIGHT_OUTPUT": A(fg="green", bg="bg_visual_green"),
    "CONSOLE_YELLOW_BRIGHT_OUTPUT": A(fg="yellow", bg="bg_visual_yellow"),
    "CONSOLE_BLUE_BRIGHT_OUTPUT": A(fg="blue", bg="bg_visual_blue"),
    "CONSOLE_MAGENTA_BRIGHT_OUTPUT": A(fg="purple", bg="bg_visual_purple"),
    "CONSOLE_CYAN_BRIGHT_OUTPUT": A(fg="aqua", bg="bg_visual_blue"),
    "CONSOLE_RANGE_TO_EXECUTE": A(effect="green", effect_type=BOX),
    "LOG_ERROR_OUTPUT": A(fg="red"),
    "LOG_WARNING_OUTPUT": A(fg="yellow"),
    "LOG_INFO_OUTPUT": A(fg="green"),
    "LOG_DEBUG_OUTPUT": A(fg="aqua"),
    "LOG_VERBOSE_OUTPUT": A(fg="grey1"),
    "LOG_EXPIRED_ENTRY": A(fg="grey0"),
    # Block terminal: not covered by the blue exception, so its blue is tan.
    "BLOCK_TERMINAL_BLACK": A(fg="bg5", bg="bg1"),
    "BLOCK_TERMINAL_RED": A(fg="red", bg="bg_visual_red"),
    "BLOCK_TERMINAL_GREEN": A(fg="green", bg="bg_visual_green"),
    "BLOCK_TERMINAL_YELLOW": A(fg="yellow", bg="bg_visual_yellow"),
    "BLOCK_TERMINAL_BLUE": A(fg="tan", bg="bg_visual_blue"),
    "BLOCK_TERMINAL_MAGENTA": A(fg="purple", bg="bg_visual_purple"),
    "BLOCK_TERMINAL_CYAN": A(fg="aqua", bg="bg_visual_blue"),
    "BLOCK_TERMINAL_WHITE": A(fg="fg0", bg="bg5"),
    "BLOCK_TERMINAL_BLACK_BRIGHT": A(fg="grey0", bg="bg3"),
    "BLOCK_TERMINAL_RED_BRIGHT": A(fg="red", bg="bg_visual_red"),
    "BLOCK_TERMINAL_GREEN_BRIGHT": A(fg="green", bg="bg_visual_green"),
    "BLOCK_TERMINAL_YELLOW_BRIGHT": A(fg="yellow", bg="bg_visual_yellow"),
    "BLOCK_TERMINAL_BLUE_BRIGHT": A(fg="tan", bg="bg_visual_blue"),
    "BLOCK_TERMINAL_MAGENTA_BRIGHT": A(fg="purple", bg="bg_visual_purple"),
    "BLOCK_TERMINAL_CYAN_BRIGHT": A(fg="aqua", bg="bg_visual_blue"),
    "BLOCK_TERMINAL_WHITE_BRIGHT": A(fg="fg0", bg="bg5"),
    "BLOCK_TERMINAL_COMMAND": A(fg="fg0"),
    "BLOCK_TERMINAL_SEARCH_ENTRY": A(bg="search"),
    "BLOCK_TERMINAL_CURRENT_SEARCH_ENTRY": A(bg="search_current"),
    # Breadcrumbs.
    "BREADCRUMBS_DEFAULT": A(fg="grey2"),
    "BREADCRUMBS_HOVERED": A(fg="fg0", bg="bg1"),
    "BREADCRUMBS_CURRENT": A(fg="fg0", bg="bg1"),
    "BREADCRUMBS_INACTIVE": A(fg="grey1"),
}

# ---------------------------------------------------------------- languages the user works in
LANGUAGES = {
    # Java
    "ANNOTATION_NAME_ATTRIBUTES": L("DEFAULT_METADATA"),
    "ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES": L("DEFAULT_PARAMETER"),
    "TYPE_PARAMETER_NAME_ATTRIBUTES": L("DEFAULT_CLASS_REFERENCE"),
    "IMPLICIT_ANONYMOUS_CLASS_PARAMETER_ATTRIBUTES": A(fg="fg0", effect="grey1", effect_type=LINE),
    "Class": L("DEFAULT_CLASS_NAME"),
    # Kotlin
    "KOTLIN_LABEL": L("DEFAULT_LABEL"),
    "KOTLIN_NAMED_ARGUMENT": L("DEFAULT_PARAMETER"),
    "KOTLIN_TYPE_PARAMETER": L("TYPE_PARAMETER_NAME_ATTRIBUTES"),
    "KOTLIN_FUNCTION_LITERAL_BRACES_AND_ARROW": L("DEFAULT_BRACES"),
    "KOTLIN_CLOSURE_DEFAULT_PARAMETER": L("DEFAULT_PARAMETER"),
    "KOTLIN_BACKING_FIELD_VARIABLE": L("DEFAULT_INSTANCE_FIELD"),
    "KOTLIN_PACKAGE_FUNCTION_CALL": L("DEFAULT_FUNCTION_CALL"),
    "KOTLIN_MUTABLE_VARIABLE": A(effect="grey1", effect_type=LINE),
    "KOTLIN_PROPERTY_WITH_BACKING_FIELD": NONE,
    "KOTLIN_SMART_CAST_VALUE": A(bg="bg_visual_green"),
    "KOTLIN_SMART_CAST_RECEIVER": A(bg="bg_visual_green"),
    "KOTLIN_SMART_CONSTANT": A(bg="bg_visual_green"),
    # Groovy / Gradle
    "Groovy method declaration": L("DEFAULT_FUNCTION_DECLARATION"),
    "Closure braces": L("DEFAULT_BRACES"),
    "Static method access": L("DEFAULT_STATIC_METHOD"),
    "Static property reference ID": L("DEFAULT_STATIC_FIELD"),
    "Unresolved reference access": A(fg="grey2", effect="grey0", effect_type=BOLD_DOTTED),
    "List/map to object conversion": A(fg="yellow"),
    "GROOVY_KEYWORD": L("DEFAULT_KEYWORD"),
    "Instance property reference ID": L("DEFAULT_INSTANCE_FIELD"),
    # JavaScript / TypeScript / Angular
    "JS.LOCAL_VARIABLE": L("DEFAULT_LOCAL_VARIABLE"),
    "JS.PARAMETER": L("DEFAULT_PARAMETER"),
    "JS.GLOBAL_VARIABLE": L("DEFAULT_GLOBAL_VARIABLE"),
    "JS.GLOBAL_FUNCTION": L("DEFAULT_FUNCTION_DECLARATION"),
    "JS.INSTANCE_MEMBER_FUNCTION": L("DEFAULT_INSTANCE_METHOD"),
    "JS.REGEXP": A(fg="green"),
    "JS.JSX_CLIENT_COMPONENT": L("DEFAULT_CLASS_REFERENCE"),
    "TS.TYPE_PARAMETER": L("TYPE_PARAMETER_NAME_ATTRIBUTES"),
    "TS.TYPE_GUARD": A(bg="bg_visual_green"),
    "NG.SIGNAL": L("DEFAULT_FUNCTION_CALL"),
    # HTML / XML (custom tags = components, which nvim captures as @type)
    "HTML_TAG": A(fg="green"),
    "HTML_TAG_NAME": L("DEFAULT_TAG"),
    "HTML_CUSTOM_TAG_NAME": A(fg="yellow"),
    "HTML_ATTRIBUTE_NAME": L("DEFAULT_ATTRIBUTE"),
    "HTML_ATTRIBUTE_VALUE": L("DEFAULT_STRING"),
    "HTML_ENTITY_REFERENCE": L("DEFAULT_ENTITY"),
    "XML_TAG": A(fg="green"),
    "XML_TAG_NAME": L("DEFAULT_TAG"),
    "XML_CUSTOM_TAG_NAME": A(fg="yellow"),
    "XML_ATTRIBUTE_NAME": L("DEFAULT_ATTRIBUTE"),
    "XML_ENTITY_REFERENCE": L("DEFAULT_ENTITY"),
    "XML_PROLOGUE": A(fg="purple"),
    # CSS / SCSS / Less
    "CSS.COLOR": A(fg="purple"),
    "CSS.IMPORTANT": L("DEFAULT_KEYWORD"),
    "CSS.URL": A(fg="tan", effect="tan", effect_type=LINE),
    "SASS_VARIABLE": L("DEFAULT_GLOBAL_VARIABLE"),
    "LESS_VARIABLE": L("DEFAULT_GLOBAL_VARIABLE"),
    "SASS_CONSTANT": L("DEFAULT_CONSTANT"),
    "SASS_MIXIN": L("DEFAULT_FUNCTION_CALL"),
    "SASS_DIRECTIVE": L("DEFAULT_KEYWORD"),
    "SASS_COMMENT": L("DEFAULT_LINE_COMMENT"),
    "SASS_RULE": L("DEFAULT_TAG"),
    "SASS_ATTRIBUTE": L("DEFAULT_INSTANCE_FIELD"),
    # Regexp (as Islands: follow the core brackets/escapes)
    "REGEXP.BRACES": L("DEFAULT_BRACES"),
    "REGEXP.BRACKETS": L("DEFAULT_BRACKETS"),
    "REGEXP.PARENTHS": L("DEFAULT_PARENTHS"),
    "REGEXP.ESC_CHARACTER": L("DEFAULT_VALID_STRING_ESCAPE"),
    "REGEXP.QUOTE_CHARACTER": L("DEFAULT_VALID_STRING_ESCAPE"),
    "REGEXP.META": L("DEFAULT_KEYWORD"),
    "REGEXP.CHAR_CLASS": A(fg="yellow"),
    "REGEXP.REDUNDANT_ESCAPE": A(fg="grey1"),
    # Go
    "GO_BUILTIN_FUNCTION_CALL": A(fg="green"),
    "GO_BUILTIN_CONSTANT": L("DEFAULT_PREDEFINED_SYMBOL"),
    "GO_BUILTIN_VARIABLE": L("DEFAULT_PREDEFINED_SYMBOL"),
    "GO_BUILTIN_TYPE_REFERENCE": L("DEFAULT_CLASS_REFERENCE"),
    "GO_TYPE_REFERENCE": L("DEFAULT_CLASS_REFERENCE"),
    "GO_EXPORTED_FUNCTION_CALL": L("DEFAULT_FUNCTION_CALL"),
    "GO_LOCAL_FUNCTION_CALL": L("DEFAULT_FUNCTION_CALL"),
    "GO_METHOD_RECEIVER": L("DEFAULT_PARAMETER"),
    "GO_PACKAGE": A(fg="yellow"),
    "GO_COMMENT_REFERENCE": A(fg="aqua"),
    "GO_SHADOWING_VARIABLE": A(fg="fg0", effect="orange", effect_type=LINE),
    "GO_SYNTAX_UPDATE": A(effect="tan", effect_type=WAVE),
    # SQL
    "SQL_SYNTHETIC_ENTITY": L("DEFAULT_CLASS_REFERENCE"),
    "SQL_OUTER_QUERY_COLUMN": A(fg="tan", effect="tan", effect_type=LINE),
    # YAML / Properties / .env
    "YAML_ANCHOR": L("DEFAULT_LABEL"),
    "PROPERTIES.KEY": L("DEFAULT_INSTANCE_FIELD"),
    "PROPERTIES.KEY_VALUE_SEPARATOR": L("DEFAULT_OPERATION_SIGN"),
    "PROPERTIES.VALID_STRING_ESCAPE": L("DEFAULT_VALID_STRING_ESCAPE"),
    "PROPERTIES.INVALID_STRING_ESCAPE": L("DEFAULT_INVALID_STRING_ESCAPE"),
    "GROUP_KEY": L("PROPERTIES.KEY"),
    # Markdown
    "MARKDOWN_HEADER": A(fg="orange"),
    "MARKDOWN_HEADER_BOLD": L("MARKDOWN_HEADER"),
    "MARKDOWN_LINK_TEXT": A(fg="aqua"),
    "MARKDOWN_AUTO_LINK": A(fg="tan", effect="tan", effect_type=LINE),
    "MARKDOWN_IMAGE": NONE,
    # nvim TSStrong is yellow; italic renders plain (enable_italic = 0)
    "MARKDOWN_BOLD": A(fg="yellow"),
    "MARKDOWN_ITALIC": NONE,
    "MARKDOWN_REFERENCE_LINK": L("MARKDOWN_LINK_TEXT"),
    # GitHub alerts; the title is the only key, NOTE's blue is tan
    "MARKDOWN_ALERT_TITLE_NOTE": A(fg="tan", bg="bg_visual_blue"),
    "MARKDOWN_ALERT_TITLE_TIP": A(fg="green", bg="bg_visual_green"),
    "MARKDOWN_ALERT_TITLE_IMPORTANT": A(fg="purple", bg="bg_visual_purple"),
    "MARKDOWN_ALERT_TITLE_WARNING": A(fg="yellow", bg="bg_visual_yellow"),
    "MARKDOWN_ALERT_TITLE_CAUTION": A(fg="red", bg="bg_visual_red"),
    # TextMate markup, as the Markdown keys
    "markup.heading": L("MARKDOWN_HEADER"),
    "markup.bold": A(fg="yellow"),
    "markup.italic": A(fg="fg0"),
    "markup.underline": A(effect="grey2", effect_type=LINE),
    # Grazie
    "TEXT_BOLD": NONE,
    "TEXT_STRIKEOUT": A(fg="grey1", effect="grey1", effect_type=STRIKE),
    "MERMAID_CONSTANT": L("DEFAULT_CONSTANT"),
    # Shell
    "BASH.EXTERNAL_COMMAND": L("DEFAULT_FUNCTION_CALL"),
    "BASH.SHEBANG": L("DEFAULT_LINE_COMMENT"),
    "BASH.HERE_DOC_START": L("DEFAULT_LABEL"),
    "BASH.HERE_DOC_END": L("DEFAULT_LABEL"),
    "BASH.FUNCTION_CALL": L("DEFAULT_FUNCTION_CALL"),
    "BASH.FUNCTION_DEF_NAME": L("DEFAULT_FUNCTION_DECLARATION"),
    "BASH.INTERNAL_COMMAND": L("DEFAULT_FUNCTION_CALL"),
    # HTTP Client
    "HTTP_REQUEST_MULTIPART_BOUNDARY": A(fg="grey1"),
    "HTTP_REQUEST_PARAMETER_NAME": L("DEFAULT_INSTANCE_FIELD"),
    "HTTP_REQUEST_PARAMETER_VALUE": L("DEFAULT_STRING"),
    # Jupyter structure view
    "STRUCTURE_VIEW_CODE_CELL_ATTRIBUTES": A(fg="grey2"),
    "STRUCTURE_VIEW_MARKDOWN_HEADER_CELL_ATTRIBUTES": NONE,
    "STRUCTURE_VIEW_MARKDOWN_TEXT_CELL_ATTRIBUTES": NONE,
    "STRUCTURE_VIEW_RAW_CELL_ATTRIBUTES": NONE,
    # Rust: each RsColor key follows its coded fallback (RsColor <clinit>, RsColor chains collapsed)
    "org.rust.ASSOC_FUNCTION": L("DEFAULT_STATIC_METHOD"),
    "org.rust.ASSOC_FUNCTION_CALL": L("DEFAULT_STATIC_METHOD"),
    "org.rust.ASSOC_TRAIT_FUNCTION": L("DEFAULT_STATIC_METHOD"),
    "org.rust.ASSOC_TRAIT_FUNCTION_CALL": L("DEFAULT_STATIC_METHOD"),
    "org.rust.CRATE": L("DEFAULT_IDENTIFIER"),
    "org.rust.DOC_CODE": L("DEFAULT_DOC_MARKUP"),
    "org.rust.ENUM": L("DEFAULT_CLASS_NAME"),
    "org.rust.ENUM_VARIANT": L("DEFAULT_STATIC_FIELD"),
    "org.rust.FUNCTION": L("DEFAULT_FUNCTION_DECLARATION"),
    "org.rust.FUNCTION_CALL": L("DEFAULT_FUNCTION_CALL"),
    "org.rust.INLINE_ERROR_DESCRIPTION": L("DEFAULT_LINE_COMMENT"),
    "org.rust.INLINE_EXPLANATION": L("DEFAULT_LINE_COMMENT"),
    "org.rust.INLINE_WARNING_DESCRIPTION": L("DEFAULT_LINE_COMMENT"),
    "org.rust.LIFETIME": L("DEFAULT_IDENTIFIER"),
    "org.rust.MACRO": L("DEFAULT_IDENTIFIER"),
    "org.rust.METHOD": L("DEFAULT_INSTANCE_METHOD"),
    "org.rust.METHOD_CALL": L("DEFAULT_FUNCTION_CALL"),
    "org.rust.MUT_BINDING": L("DEFAULT_REASSIGNED_LOCAL_VARIABLE"),
    "org.rust.MUT_PARAMETER": L("DEFAULT_REASSIGNED_PARAMETER"),
    "org.rust.MUT_SELF_PARAMETER": L("DEFAULT_REASSIGNED_PARAMETER"),
    "org.rust.PARAMETER": L("DEFAULT_PARAMETER"),
    "org.rust.Q_OPERATOR": L("DEFAULT_KEYWORD"),
    "org.rust.SELF_EXPRESSION": L("DEFAULT_KEYWORD"),
    "org.rust.SELF_PARAMETER": L("DEFAULT_KEYWORD"),
    "org.rust.STATIC": L("DEFAULT_IDENTIFIER"),
    "org.rust.STRUCT": L("DEFAULT_CLASS_NAME"),
    "org.rust.TRAIT": L("DEFAULT_INTERFACE_NAME"),
    "org.rust.TRAIT_METHOD": L("DEFAULT_INSTANCE_METHOD"),
    "org.rust.TRAIT_METHOD_CALL": L("DEFAULT_FUNCTION_CALL"),
    "org.rust.TYPE_ALIAS": L("DEFAULT_CLASS_NAME"),
    "org.rust.TYPE_PARAMETER": L("DEFAULT_IDENTIFIER"),
    "org.rust.UNION": L("DEFAULT_CLASS_NAME"),
    "org.rust.CFG_DISABLED_CODE": A(fg="grey1"),
    # Docker / Compose
    "COMPOSE_SERVICE_STATUS_ERROR": A(fg="red"),
    "COMPOSE_SERVICE_STATUS_SUCCESS": A(fg="green"),
    "COMPOSE_SERVICE_STATUS_NEUTRAL": A(fg="grey2"),
    # GitToolBox inline blame: one dim line, like a comment
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_ATTRIBUTES": A(fg="grey0"),
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_AUTHOR_ATTRIBUTES": A(fg="grey0"),
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_TIMESTAMP_ATTRIBUTES": A(fg="grey0"),
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_SUBJECT_ATTRIBUTES": A(fg="grey0"),
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_ISSUE_REFERENCE_ATTRIBUTES": A(fg="grey1"),
    "GIT_TOOLBOX.EDITOR_INLINE_BLAME_ISSUE_LINK_ATTRIBUTES": A(fg="grey1", effect="grey0", effect_type=LINE),
    # .gitignore
    "IGNORE.COMMENT": L("DEFAULT_LINE_COMMENT"),
    "IGNORE.SECTION": A(fg="grey1", bg="bg1"),
    "IGNORE.HEADER": A(fg="grey1", bg="bg1"),
    "IGNORE.NEGATION": L("DEFAULT_KEYWORD"),
    "IGNORE.BRACKET": L("DEFAULT_BRACKETS"),
    "IGNORE.SLASH": L("DEFAULT_DOT"),
    "IGNORE.SYNTAX": L("DEFAULT_KEYWORD"),
    "IGNORE.VALUE": L("DEFAULT_STRING"),
    "IGNORE.UNUSED_ENTRY": L("NOT_USED_ELEMENT_ATTRIBUTES"),
}

# ---------------------------------------------------------------- level sets that must stay distinguishable
# Rainbow Brackets: the outermost level is plain text, then accents far apart in hue; no red or orange, which the
# keyword and operator colours own.
RAINBOW = ["fg0", "aqua", "yellow", "purple", "green", "tan", "grey2"]
CYCLES = [
    (r"^(ROUND|SQUARE|SQUIGGLY|ANGLE)_BRACKETS_RAINBOW_COLOR(\d+)$", RAINBOW),
    (r"^(INDENT_GUIDES)_RAINBOW_COLOR(\d+)$", RAINBOW),
    (r"^(RAINBOW)_COLOR(\d+)$", ["aqua", "orange", "green", "purple", "yellow"]),
    (r"^(CSV_PLUGIN_COLUMN_COLORING_ATTRIBUTE)_(\d+)$",
     ["yellow", "red", "purple", "aqua", "grey2", "green", "tan", "orange", "fg0", "grey1"]),
]

# Islands' chrome greys by role (its editor is darker than ours), applied before the generic mapping.
ISLANDS_GREYS = {
    "191a1c": "bg0",  # editor, console
    "1f2024": "bg1",  # caret row
    "26292c": "bg1",  # doc code block
    "27282b": "bg1",  # popups
    "27292b": "bg1",
    "2b2d30": "bg_current_word",  # separators, hint panes
    "323438": "bg1",  # indent guide, right margin
    "343539": "bg_current_word",
    "393b40": "bg3",  # inlays, folded, hint border
    "3f4045": "bg3",
    "43454a": "bg3",
    "4e5157": "bg5",
}

# ---------------------------------------------------------------- alignment with the nvim dump
# (nvim group, nvim field, IntelliJ key, IntelliJ field). generate.py resolves both sides and reports mismatches.
NVIM_ALIGN = [
    ("Normal", "fg", "TEXT", "FOREGROUND"),
    ("Normal", "bg", "TEXT", "BACKGROUND"),
    ("Comment", "fg", "DEFAULT_LINE_COMMENT", "FOREGROUND"),
    ("@keyword", "fg", "DEFAULT_KEYWORD", "FOREGROUND"),
    ("@keyword.return", "fg", "DEFAULT_KEYWORD", "FOREGROUND"),
    ("@operator", "fg", "DEFAULT_OPERATION_SIGN", "FOREGROUND"),
    ("@punctuation.bracket", "fg", "DEFAULT_PARENTHS", "FOREGROUND"),
    ("@punctuation.delimiter", "fg", "DEFAULT_COMMA", "FOREGROUND"),
    ("@string", "fg", "DEFAULT_STRING", "FOREGROUND"),
    ("@string.escape", "fg", "DEFAULT_VALID_STRING_ESCAPE", "FOREGROUND"),
    ("@string.regexp", "fg", "JS.REGEXP", "FOREGROUND"),
    ("@number", "fg", "DEFAULT_NUMBER", "FOREGROUND"),
    ("@constant", "fg", "DEFAULT_CONSTANT", "FOREGROUND"),
    ("@constant.builtin", "fg", "DEFAULT_PREDEFINED_SYMBOL", "FOREGROUND"),
    ("@function", "fg", "DEFAULT_FUNCTION_DECLARATION", "FOREGROUND"),
    ("@function.call", "fg", "DEFAULT_FUNCTION_CALL", "FOREGROUND"),
    ("@function.builtin", "fg", "GO_BUILTIN_FUNCTION_CALL", "FOREGROUND"),
    ("@function.method", "fg", "DEFAULT_INSTANCE_METHOD", "FOREGROUND"),
    ("@type", "fg", "DEFAULT_CLASS_NAME", "FOREGROUND"),
    ("@type.builtin", "fg", "GO_BUILTIN_TYPE_REFERENCE", "FOREGROUND"),
    ("@variable", "fg", "DEFAULT_LOCAL_VARIABLE", "FOREGROUND"),
    ("@variable.parameter", "fg", "DEFAULT_PARAMETER", "FOREGROUND"),
    ("@variable.member", "fg", "DEFAULT_INSTANCE_FIELD", "FOREGROUND"),
    ("@attribute", "fg", "DEFAULT_METADATA", "FOREGROUND"),
    ("@label", "fg", "DEFAULT_LABEL", "FOREGROUND"),
    ("@module", "fg", "GO_PACKAGE", "FOREGROUND"),
    ("@tag", "fg", "DEFAULT_TAG", "FOREGROUND"),
    ("@tag.attribute", "fg", "DEFAULT_ATTRIBUTE", "FOREGROUND"),
    ("@tag.delimiter", "fg", "HTML_TAG", "FOREGROUND"),
    ("@markup.heading", "fg", "MARKDOWN_HEADER", "FOREGROUND"),
    ("@markup.link", "fg", "MARKDOWN_LINK_TEXT", "FOREGROUND"),
    ("@markup.link.url", "fg", "HYPERLINK_ATTRIBUTES", "FOREGROUND"),
    ("Todo", "bg", "TODO_DEFAULT_ATTRIBUTES", "FOREGROUND"),
    ("DiagnosticError", "fg", "ERRORS_ATTRIBUTES", "EFFECT_COLOR"),
    ("DiagnosticWarn", "fg", "WARNING_ATTRIBUTES", "EFFECT_COLOR"),
    ("DiagnosticInfo", "fg", "WEAK_WARNING_ATTRIBUTES", "EFFECT_COLOR"),
    ("DiagnosticHint", "fg", "INFO_ATTRIBUTES", "EFFECT_COLOR"),
    ("DiagnosticUnnecessary", "fg", "NOT_USED_ELEMENT_ATTRIBUTES", "FOREGROUND"),
    ("DiagnosticDeprecated", "sp", "DEPRECATED_ATTRIBUTES", "EFFECT_COLOR"),
    ("SpellBad", "sp", "TYPO", "EFFECT_COLOR"),
    ("SpellCap", "sp", "GRAMMAR_ERROR", "EFFECT_COLOR"),
    ("DiffAdd", "bg", "DIFF_INSERTED", "BACKGROUND"),
    ("DiffDelete", "bg", "DIFF_DELETED", "BACKGROUND"),
    # DiffChange tints the changed line, DiffText the changed text in it; IntelliJ's line tint is FOREGROUND.
    ("DiffChange", "bg", "DIFF_MODIFIED", "FOREGROUND"),
    ("DiffText", "bg", "DIFF_MODIFIED", "BACKGROUND"),
    ("Added", "fg", "ADDED_LINES_COLOR", None),
    ("Changed", "fg", "MODIFIED_LINES_COLOR", None),
    ("Removed", "fg", "DELETED_LINES_COLOR", None),
    ("Search", "bg", "TEXT_SEARCH_RESULT_ATTRIBUTES", "BACKGROUND"),
    ("CurSearch", "bg", "BLOCK_TERMINAL_CURRENT_SEARCH_ENTRY", "BACKGROUND"),
    ("LspReferenceText", "bg", "IDENTIFIER_UNDER_CARET_ATTRIBUTES", "BACKGROUND"),
    ("LspReferenceWrite", "bg", "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES", "BACKGROUND"),
    ("LspInlayHint", "fg", "INLAY_DEFAULT", "FOREGROUND"),
    ("Visual", "bg", "SELECTION_BACKGROUND", None),
    ("CursorLine", "bg", "CARET_ROW_COLOR", None),
    ("ColorColumn", "bg", "RIGHT_MARGIN_COLOR", None),
    ("LineNr", "fg", "LINE_NUMBERS_COLOR", None),
    ("CursorLineNr", "fg", "LINE_NUMBER_ON_CARET_ROW_COLOR", None),
    ("MatchParen", "bg", "MATCHED_BRACE_ATTRIBUTES", "BACKGROUND"),
    ("Folded", "fg", "FOLDED_TEXT_ATTRIBUTES", "FOREGROUND"),
    ("Folded", "bg", "FOLDED_TEXT_ATTRIBUTES", "BACKGROUND"),
    ("NonText", "fg", "WHITESPACES", None),
    ("IblIndent", "fg", "INDENT_GUIDE", None),
]

# Deliberate departures from nvim, reported instead of flagged.
NVIM_DEVIATIONS = {
    ("Todo", "TODO_DEFAULT_ATTRIBUTES"): "nvim paints a solid tan block; here tan text, no block",
    ("LspReferenceWrite", "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES"): "write usages get the write_usage tint so they differ from reads",
    ("LspInlayHint", "INLAY_DEFAULT"): "grey0 instead of bg5: inlays sit on a bg1 pill",
    ("IblIndent", "INDENT_GUIDE"): "bg3 instead of bg5: continuous guide lines read brighter than nvim's glyphs",
    ("Changed", "MODIFIED_LINES_COLOR"): "yellow instead of tan: modified markers follow the amber diff hue",
}
