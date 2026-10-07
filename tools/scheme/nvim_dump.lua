-- Dumps the effective (link-resolved) colors of the nvim highlight groups the scheme mirrors.
-- Run by generate.py --refresh-nvim from the nvim config dir; prints JSON on stdout.
local groups = {
  "Normal","NormalFloat","Comment","@keyword","@keyword.function","@keyword.return","@keyword.conditional","@conditional","@keyword.repeat","@repeat","@keyword.import","@keyword.operator","@operator","@punctuation.delimiter","@punctuation.bracket","@punctuation.special","@string","@string.escape","@string.regexp","@string.special","@character","@number","@number.float","@boolean","@constant","@constant.builtin","@constant.macro","@function","@function.call","@function.builtin","@function.method","@function.method.call","@method","@constructor","@type","@type.builtin","@type.definition","@variable","@variable.builtin","@variable.parameter","@variable.member","@property","@field","@attribute","@annotation","@label","@module","@namespace","@tag","@tag.attribute","@tag.delimiter","@markup.heading","@markup.link","@markup.link.url","@markup.raw","@markup.list","@markup.quote","@comment.todo","Todo","DiagnosticError","DiagnosticWarn","DiagnosticInfo","DiagnosticHint","DiagnosticUnderlineError","DiagnosticUnderlineWarn","DiagnosticUnderlineInfo","DiagnosticUnderlineHint","DiagnosticDeprecated","DiagnosticUnnecessary","DiffAdd","DiffDelete","DiffChange","DiffText","Added","Changed","Removed","Search","IncSearch","CurSearch","Substitute","Visual","CursorLine","ColorColumn","LineNr","CursorLineNr","SignColumn","MatchParen","Folded","NonText","Whitespace","SpellBad","SpellCap","LspReferenceText","LspReferenceRead","LspReferenceWrite","LspInlayHint","Pmenu","PmenuSel","Cursor","WinSeparator","Title","Error","ErrorMsg","WarningMsg","Underlined","SnacksIndent","SnacksIndentScope","IblIndent","IblScope"
}
local out = {}
for _, n in ipairs(groups) do
  local h = vim.api.nvim_get_hl(0, { name = n, link = false })
  local e = {}
  for _, k in ipairs({ "fg", "bg", "sp" }) do
    if h[k] then e[k] = string.format("#%06x", h[k]) end
  end
  for _, k in ipairs({ "bold", "italic", "underline", "undercurl", "strikethrough", "reverse" }) do
    if h[k] then e[k] = true end
  end
  out[n] = next(e) and e or vim.empty_dict()
end
io.stdout:write(vim.json.encode({ colors_name = vim.g.colors_name, groups = out }))
