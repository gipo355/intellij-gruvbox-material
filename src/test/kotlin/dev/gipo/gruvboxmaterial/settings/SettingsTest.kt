package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.ColorKey
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.colors.impl.EditorColorsSchemeImpl
import com.intellij.openapi.editor.markup.EffectType
import com.intellij.openapi.editor.markup.TextAttributes
import com.intellij.util.xmlb.XmlSerializer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.Color
import java.awt.Font
import java.lang.reflect.Proxy
import javax.swing.UIManager

class SettingsTest {
    private val fixture = Palette.parse(FIXTURE_PALETTE, FIXTURE_GROUPS)
    private val dark = fixture.variants.getValue("variant-dark")

    private val original = mapOf(
        "DEFAULT_OPERATION_SIGN" to attributes("e78a4e"),
        "DEFAULT_LINE_COMMENT" to attributes("a89984"),
        "DEFAULT_BLOCK_COMMENT" to attributes("a89984"),
        "DEFAULT_DOC_COMMENT_TAG" to attributes("a89984"),
        "DEFAULT_DOC_MARKUP" to attributes("c4a67e", effect = "89b482"),
        "DEFAULT_FUNCTION_CALL" to attributes("a9b665"),
        "DEFAULT_KEYWORD" to attributes("ea6962"),
        "DEFAULT_PARAMETER" to attributes("d4be98"),
        "DEFAULT_REASSIGNED_LOCAL_VARIABLE" to underline(),
        "DEFAULT_REASSIGNED_PARAMETER" to underline(),
        "DEFAULT_METADATA" to attributes("d48da0"),
        "ANNOTATION_NAME_ATTRIBUTES" to attributes("d48da0"),
        "ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES" to attributes("d4be98"),
    )

    @Test
    fun parsesFixture() {
        assertEquals(setOf("variant-dark", "variant-light"), fixture.variants.keys)
        assertEquals("Fixture Dark Scheme", dark.editorScheme)
        assertTrue(dark.dark)
        assertEquals(Color(0xd4be98), dark.roles["fg0"])
        assertEquals(Color(0x80252423.toInt(), true), dark.roles["tint"])
        assertSame(dark, fixture.variantForScheme("Fixture Dark Scheme"))
        assertNull(fixture.variantForScheme("Darcula"))
        assertEquals(listOf("Component.focusColor", "*.underlineColor"), fixture.groups.accentUiKeys["material-dark"])
    }

    @Test
    fun shippedPaletteCoversEveryRoleTheFeaturesRead() {
        val shipped = Palette.load()
        val roles = listOf("fg0", "grey1", "grey2", "bg3", "bg_current_word")
        val missing = shipped.variants.values.flatMap { v -> (roles + accentChoices(v)).filter { it !in v.roles }.map { "${v.id}: $it" } }
        assertTrue("missing roles: $missing", missing.isEmpty())
        for (v in shipped.variants.values) {
            assertEquals(v.name, accentChoices(v).first(), shipped.groups.accentRole[v.schemeFamily])
            assertTrue(v.name, v.schemeFamily in shipped.groups.styles && v.schemeFamily in shipped.groups.keyGroups)
        }
        assertTrue(shipped.groups.operators.isNotEmpty() && shipped.groups.comments.isNotEmpty())
        assertTrue(shipped.variants.values.all { !shipped.groups.accentUiKeys[it.schemeFamily].isNullOrEmpty() && it.schemeFamily in shipped.groups.schemeForegroundRoles })
        assertTrue("PARAMETER_ATTRIBUTES" in shipped.groups.parameters && "TYPE_PARAMETER_NAME_ATTRIBUTES" !in shipped.groups.parameters)
        assertTrue("DEFAULT_REASSIGNED_LOCAL_VARIABLE" in shipped.groups.reassigned)
        val annotations = shipped.groups.annotations
        assertTrue(annotations.toString(), listOf("DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES", "KOTLIN_ANNOTATION", "TS.DECORATOR", "PY.DECORATOR").all { it in annotations })
        assertTrue(annotations.toString(), annotations.none { "ATTRIBUTE_NAME" in it } && "KOTLIN_BUILTIN_ANNOTATION" !in annotations)
    }

    @Test
    fun everyToggleOffChangesNothing() {
        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability()).isEmpty())
    }

    @Test
    fun togglesRecolorOnlyTheForeground() {
        val all = readabilityOverrides(original, fixture.groups, dark.roles, Readability(true, false, true, true))
        assertEquals(Color(0xa89984), all.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        assertEquals(Color(0xd4be98), all.getValue("DEFAULT_FUNCTION_CALL").foregroundColor)
        // Docs take the comment colour; the tag already has it, so only the markup changes.
        assertEquals(setOf("DEFAULT_OPERATION_SIGN", "DEFAULT_DOC_MARKUP", "DEFAULT_FUNCTION_CALL"), all.keys)
        val markup = all.getValue("DEFAULT_DOC_MARKUP")
        assertEquals(Color(0xa89984), markup.foregroundColor)
        assertEquals(Color(0x89b482), markup.effectColor)
        assertEquals(EffectType.LINE_UNDERSCORE, markup.effectType)
        assertEquals(Font.PLAIN, markup.fontType)
        assertEquals(Color(0xc4a67e), original.getValue("DEFAULT_DOC_MARKUP").foregroundColor)
    }

    @Test
    fun dimmedCommentsPullDocsAlong() {
        val dimmed = readabilityOverrides(original, fixture.groups, dark.roles, Readability(dimComments = true, softenDocs = true))
        val grey1 = Color(0x928374)
        assertEquals(listOf("DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT", "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_MARKUP"), dimmed.keys.toList())
        assertTrue(dimmed.values.all { it.foregroundColor == grey1 })
    }

    @Test
    fun keysTheSchemeDoesNotDefineAreSkipped() {
        val overrides = readabilityOverrides(mapOf("DEFAULT_LINE_COMMENT" to attributes("a89984")), fixture.groups, dark.roles, Readability(true, true, true, true))
        assertEquals(setOf("DEFAULT_LINE_COMMENT"), overrides.keys)
    }

    @Test
    fun restoreBringsBackTheExactOriginals() {
        val stored = original.mapKeys { TextAttributesKey.find(it.key) }.toMutableMap()
        val before = stored.toMap()
        val scheme = fakeScheme(stored)
        val overrides = SchemeOverrides()

        overrides.apply(scheme, readabilityOverrides(original, fixture.groups, dark.roles, Readability(true, true, true, true)))
        overrides.apply(scheme, readabilityOverrides(original, fixture.groups, dark.roles, Readability(dimComments = true)))
        assertEquals(Color(0x928374), stored.getValue(TextAttributesKey.find("DEFAULT_LINE_COMMENT")).foregroundColor)

        overrides.restore()
        assertTrue(overrides.isEmpty)
        for ((key, attributes) in before) {
            assertSame(key.externalName, attributes, stored[key])
            assertEquals(key.externalName, original.getValue(key.externalName), stored[key])
        }
    }

    @Test
    fun editableCopyInheritsOverridesAndStaysClean() {
        val shipped = EditorColorsSchemeImpl(null)
        val comment = TextAttributesKey.find("DEFAULT_LINE_COMMENT")
        val lineNumbers = ColorKey.find("LINE_NUMBERS_COLOR")
        val shippedComment = original.getValue("DEFAULT_LINE_COMMENT")
        for ((name, attributes) in original) shipped.setAttributes(TextAttributesKey.find(name), attributes)
        shipped.setColor(lineNumbers, Color(0x5a524c))
        val copy = EditorColorsSchemeImpl(shipped)
        val overrides = SchemeOverrides()

        overrides.apply(copy, readabilityOverrides(original, fixture.groups, dark.roles, Readability(dimComments = true)))
        overrides.applyColors(copy, mapOf("LINE_NUMBERS_COLOR" to Color(0x7c6f64)))
        assertEquals(Color(0x928374), copy.getAttributes(comment).foregroundColor)
        assertEquals(Color(0x7c6f64), copy.getColor(lineNumbers))
        assertTrue(copy.directlyDefinedAttributes.isEmpty() && copy.directlyDefinedColors.isEmpty())

        overrides.restore()
        assertSame(shippedComment, shipped.getDirectlyDefinedAttributes(comment))
        assertEquals(Color(0x5a524c), copy.getColor(lineNumbers))
        assertTrue(copy.directlyDefinedAttributes.isEmpty() && copy.directlyDefinedColors.isEmpty())
    }

    @Test
    fun keywordTableLookup() {
        assertNull(keywordColor(dark, KeywordChoice()))
        assertEquals(Color(0xd4be98), keywordColor(dark, KeywordChoice(PLAIN, brightness = 5, strength = 2)))
        assertEquals(Color(0xcd936a), keywordColor(dark, KeywordChoice("orange", brightness = 1, strength = 1)))
        assertEquals(Color(0xda8d53), keywordColor(dark, KeywordChoice("orange", brightness = 0, strength = 0)))
        assertNull(keywordColor(dark, KeywordChoice("orange", brightness = 2)))
        assertNull(keywordColor(dark, KeywordChoice("slate")))
        assertNull(keywordColor(fixture.variants.getValue("variant-light"), KeywordChoice("orange")))
        assertTrue(KeywordChoice("orange").tunable)
        assertTrue(!KeywordChoice(STOCK).tunable && !KeywordChoice(PLAIN).tunable)
    }

    @Test
    fun shippedKeywordTableMatchesTheFormula() {
        val shipped = Palette.load()
        for (variant in shipped.variants.values) {
            // the reference hexes are dark; light solves its own lightness per entry
            if (variant.dark) {
                assertEquals(Color(0xcd936a), keywordColor(variant, KeywordChoice("orange")))
                assertEquals(Color(0xd48b85), keywordColor(variant, KeywordChoice("red")))
            }
            assertEquals((KEYWORD_FAMILIES - STOCK - PLAIN).toSet(), variant.keywords!!.families.keys)
            assertTrue(variant.keywords!!.families.values.all { f -> f.colors.size == 7 && f.colors.all { it.size == 3 } })
        }
        assertTrue("DEFAULT_KEYWORD" in shipped.groups.keywords)
    }

    @Test
    fun keywordFamilyMovesOperatorsToForegroundUnlessQuietOrKept() {
        val orange = Color(0xcd936a)
        val kept = readabilityOverrides(original, fixture.groups, dark.roles, Readability(), orange, "orange")
        assertEquals(setOf("DEFAULT_KEYWORD"), kept.keys)

        val coupled = readabilityOverrides(original, fixture.groups, dark.roles, Readability(keepOperatorColor = false), orange, "orange")
        assertEquals(setOf("DEFAULT_OPERATION_SIGN", "DEFAULT_KEYWORD"), coupled.keys)
        assertEquals(Color(0xd4be98), coupled.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        assertEquals(orange, coupled.getValue("DEFAULT_KEYWORD").foregroundColor)

        val quiet = readabilityOverrides(original, fixture.groups, dark.roles, Readability(quietOperators = true, keepOperatorColor = false), orange, "orange")
        assertEquals(Color(0xa89984), quiet.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)

        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability(), keywordColor(dark, KeywordChoice())).isEmpty())
    }

    @Test
    fun onlyClashingKeywordFamiliesMoveOperators() {
        val color = Color(0xb0a090)
        for (family in listOf("red", "orange", "clay")) {
            val overrides = readabilityOverrides(original, fixture.groups, dark.roles, Readability(keepOperatorColor = false), color, family)
            assertEquals(family, Color(0xd4be98), overrides.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        }
        for (family in listOf("stone", "slate", PLAIN)) {
            val overrides = readabilityOverrides(original, fixture.groups, dark.roles, Readability(keepOperatorColor = false), color, family)
            assertEquals(family, setOf("DEFAULT_KEYWORD"), overrides.keys)
            val quiet = readabilityOverrides(original, fixture.groups, dark.roles, Readability(quietOperators = true), color, family)
            assertEquals(family, Color(0xa89984), quiet.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        }
    }

    @Test
    fun italicTogglesSetOnlyTheFontType() {
        val italic = readabilityOverrides(original, fixture.groups, dark.roles, Readability(italicComments = true, italicParameters = true))
        assertEquals(
            setOf("DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT", "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_MARKUP", "DEFAULT_PARAMETER", "DEFAULT_REASSIGNED_PARAMETER"),
            italic.keys,
        )
        for ((key, attributes) in italic) {
            val before = original.getValue(key)
            assertEquals(key, Font.ITALIC, attributes.fontType)
            assertEquals(key, before.foregroundColor, attributes.foregroundColor)
            assertEquals(key, before.effectType, attributes.effectType)
            assertEquals(key, before.effectColor, attributes.effectColor)
        }
        assertEquals(Font.PLAIN, original.getValue("DEFAULT_PARAMETER").fontType)
    }

    @Test
    fun italicCommentsCombineWithDimAndSoften() {
        val grey1 = Color(0x928374)
        val both = readabilityOverrides(original, fixture.groups, dark.roles, Readability(dimComments = true, softenDocs = true, italicComments = true))
        assertEquals(setOf("DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT", "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_MARKUP"), both.keys)
        assertTrue(both.values.all { it.foregroundColor == grey1 && it.fontType == Font.ITALIC })
    }

    @Test
    fun hideReassignUnderlineClearsOnlyTheEffect() {
        val hidden = readabilityOverrides(original, fixture.groups, dark.roles, Readability(hideReassignUnderline = true))
        assertEquals(setOf("DEFAULT_REASSIGNED_LOCAL_VARIABLE", "DEFAULT_REASSIGNED_PARAMETER"), hidden.keys)
        assertTrue(hidden.values.all { it.effectType == null && it.effectColor == null && it.foregroundColor == null && it.fontType == Font.PLAIN })

        // A reassigned parameter is in both groups and keeps both changes.
        val combined = readabilityOverrides(original, fixture.groups, dark.roles, Readability(italicParameters = true, hideReassignUnderline = true))
        val parameter = combined.getValue("DEFAULT_REASSIGNED_PARAMETER")
        assertEquals(Font.ITALIC, parameter.fontType)
        assertNull(parameter.effectType)
        assertEquals(Font.PLAIN, combined.getValue("DEFAULT_REASSIGNED_LOCAL_VARIABLE").fontType)
        assertEquals(EffectType.LINE_UNDERSCORE, original.getValue("DEFAULT_REASSIGNED_PARAMETER").effectType)
    }

    @Test
    fun restoreRoundTripsFontTypeAndEffect() {
        val stored = original.mapKeys { TextAttributesKey.find(it.key) }.toMutableMap()
        val before = stored.mapValues { (_, a) -> Triple(a.fontType, a.effectType, a.effectColor) }
        val overrides = SchemeOverrides()
        overrides.apply(fakeScheme(stored), readabilityOverrides(original, fixture.groups, dark.roles, Readability(dimComments = true, italicComments = true, italicParameters = true, hideReassignUnderline = true)))
        assertEquals(Font.ITALIC, stored.getValue(TextAttributesKey.find("DEFAULT_PARAMETER")).fontType)
        assertNull(stored.getValue(TextAttributesKey.find("DEFAULT_REASSIGNED_LOCAL_VARIABLE")).effectType)

        overrides.restore()
        for ((key, attributes) in stored) {
            assertSame(key.externalName, original.getValue(key.externalName), attributes)
            assertEquals(key.externalName, before.getValue(key), Triple(attributes.fontType, attributes.effectType, attributes.effectColor))
        }
    }

    @Test
    fun purpleAnnotationsAreTheShippedScheme() {
        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability()).isEmpty())
        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability(annotations = AnnotationStyle.PURPLE)).isEmpty())
        assertTrue(AnnotationStyle.entries.filter { it != AnnotationStyle.PURPLE }.all { Readability(annotations = it).any })
    }

    @Test
    fun greyAnnotationsRecolorNamesNotAttributes() {
        val names = setOf("DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES")
        val grey = readabilityOverrides(original, fixture.groups, dark.roles, Readability(annotations = AnnotationStyle.GREY))
        assertEquals(names, grey.keys)
        assertTrue(grey.values.all { it.foregroundColor == Color(0xa89984) })

        val dim = readabilityOverrides(original, fixture.groups, dark.roles, Readability(annotations = AnnotationStyle.DIM_GREY))
        assertEquals(names, dim.keys)
        assertTrue(dim.values.all { it.foregroundColor == Color(0x928374) })
    }

    @Test
    fun parameterStyleRecolorsParametersAndOrangeMovesOperators() {
        val parameters = setOf("DEFAULT_PARAMETER", "DEFAULT_REASSIGNED_PARAMETER")
        assertTrue(ParameterStyle.entries.filter { it != ParameterStyle.DEFAULT }.all { Readability(parameters = it).any })

        val aqua = readabilityOverrides(original, fixture.groups, dark.roles, Readability(parameters = ParameterStyle.AQUA))
        assertEquals(parameters, aqua.keys)
        assertTrue(aqua.values.all { it.foregroundColor == Color(0x89b482) })
        assertEquals(EffectType.LINE_UNDERSCORE, aqua.getValue("DEFAULT_REASSIGNED_PARAMETER").effectType)

        val orange = readabilityOverrides(original, fixture.groups, dark.roles, Readability(parameters = ParameterStyle.ORANGE))
        assertEquals(parameters + "DEFAULT_OPERATION_SIGN", orange.keys)
        assertEquals(Color(0xd4be98), orange.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        assertEquals(Color(0xe78a4e), orange.getValue("DEFAULT_PARAMETER").foregroundColor)

        val quiet = readabilityOverrides(original, fixture.groups, dark.roles, Readability(quietOperators = true, parameters = ParameterStyle.ORANGE))
        assertEquals(Color(0xa89984), quiet.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
    }

    @Test
    fun keywordColourAnnotationsFollowTheKeywordPicker() {
        val readability = Readability(annotations = AnnotationStyle.KEYWORD)
        val ghost = Color(0x7c6f64)
        val family = readabilityOverrides(original, fixture.groups, dark.roles, readability, ghost, "stone")
        assertEquals(setOf("DEFAULT_KEYWORD", "DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES"), family.keys)
        val keyword = family.getValue("DEFAULT_KEYWORD").foregroundColor
        assertEquals(ghost, keyword)
        assertTrue(listOf("DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES").all { family.getValue(it).foregroundColor == keyword })

        val stock = readabilityOverrides(original, fixture.groups, dark.roles, readability, keywordColor(dark, KeywordChoice()))
        assertEquals(setOf("DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES"), stock.keys)
        assertTrue(stock.values.all { it.foregroundColor == Color(0xea6962) })

        val plain = readabilityOverrides(original, fixture.groups, dark.roles, readability, keywordColor(dark, KeywordChoice(PLAIN)), PLAIN)
        assertTrue(listOf("DEFAULT_KEYWORD", "DEFAULT_METADATA", "ANNOTATION_NAME_ATTRIBUTES").all { plain.getValue(it).foregroundColor == Color(0xd4be98) })
    }

    @Test
    fun annotationStyleCombinesWithItalicsAndRestores() {
        val stored = original.mapKeys { TextAttributesKey.find(it.key) }.toMutableMap()
        val overrides = SchemeOverrides()
        val readability = Readability(annotations = AnnotationStyle.DIM_GREY, italicComments = true, italicParameters = true)
        val changed = readabilityOverrides(original, fixture.groups, dark.roles, readability)
        assertEquals(Font.ITALIC, changed.getValue("DEFAULT_PARAMETER").fontType)
        assertEquals(Font.ITALIC, changed.getValue("DEFAULT_LINE_COMMENT").fontType)
        assertEquals(Font.PLAIN, changed.getValue("ANNOTATION_NAME_ATTRIBUTES").fontType)
        overrides.apply(fakeScheme(stored), changed)
        assertEquals(Color(0x928374), stored.getValue(TextAttributesKey.find("ANNOTATION_NAME_ATTRIBUTES")).foregroundColor)
        assertSame(original.getValue("ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES"), stored.getValue(TextAttributesKey.find("ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES")))

        overrides.restore()
        for ((key, attributes) in stored) assertSame(key.externalName, original.getValue(key.externalName), attributes)
        assertEquals(Color(0xd48da0), stored.getValue(TextAttributesKey.find("DEFAULT_METADATA")).foregroundColor)
    }

    @Test
    fun backToStockRestoresTheShippedScheme() {
        val stored = original.mapKeys { TextAttributesKey.find(it.key) }.toMutableMap()
        val before = stored.toMap()
        val overrides = SchemeOverrides()
        overrides.apply(fakeScheme(stored), readabilityOverrides(original, fixture.groups, dark.roles, Readability(), Color(0xcd936a)))
        assertEquals(Color(0xcd936a), stored.getValue(TextAttributesKey.find("DEFAULT_KEYWORD")).foregroundColor)
        overrides.restore()
        for ((key, attributes) in before) assertSame(key.externalName, attributes, stored[key])
    }

    @Test
    fun contrastRatioFollowsWcag() {
        assertEquals(21.0, contrastRatio(Color.WHITE, Color.BLACK), 0.01)
        assertEquals(1.0, contrastRatio(Color(0x32302f), Color(0x32302f)), 0.0)
    }

    @Test
    fun indentRainbowPaletteIsArgbHex() {
        assertEquals("1AE78A4E, 1AD8A657, 1AA9B665, 1A89B482, 1AC4A67E, 1AD3869B", indentRainbowPalette(dark))
        assertEquals("4D802020, 4D000000", indentRainbowPalette(listOf(Color(0x802020), Color.BLACK), alpha = 0x4D))
    }

    @Test
    fun parsesTextContrastLevels() {
        assertEquals("material", dark.defaultForeground)
        assertEquals(setOf("material", "original"), dark.foregrounds.keys)
        assertEquals(dark.roles, dark.atLevel(null).roles)
        assertEquals(dark.keywords, dark.atLevel("material").keywords)
        val original = dark.atLevel("original")
        assertEquals(Color(0xebdbb2), original.roles["fg0"])
        assertEquals(dark.roles["bg0"], original.roles["bg0"])
        assertEquals(Color(0xd99f73), keywordColor(original, KeywordChoice("orange")))
        assertSame(dark, dark.atLevel("mix"))
        assertEquals(listOf(Level("material", "Material"), Level("original", "Original")), dark.levels)
        assertEquals("Default (Material)", textContrastLabel(dark, null))
        val light = fixture.variants.getValue("variant-light")
        assertEquals("material", light.paletteFamily)
        assertEquals("material-light", light.schemeFamily)
        assertEquals("Default (Mix)", textContrastLabel(light, null))
        assertEquals(Color(0x4f3829), light.atLevel("material").roles["fg0"])
        assertEquals(mapOf("FOREGROUND" to "tan", "EFFECT_COLOR" to "aqua"), fixture.groups.schemeForegroundRoles.getValue("material-dark").attributes["DEFAULT_DOC_MARKUP"])
        assertEquals("fg0", fixture.groups.schemeForegroundRoles.getValue("material-dark").colors["CARET_COLOR"])
        assertEquals(listOf("Component.focusColor", "*.underlineColor"), fixture.groups.uiForegroundKeys.getValue("material-dark")["aqua"])
        assertEquals(RoleStep("bg3", "bg5"), fixture.groups.highUiContrast.getValue("material-dark")["INDENT_GUIDE"])
    }

    @Test
    fun palettesWithoutTextContrastStillParse() {
        val old = Palette.parse("""{"variants": {"v": {"name": "V", "dark": true, "editorScheme": "S", "roles": {"fg0": "#d4be98"}}}}""", """{"operators": []}""")
        val v = old.variants.getValue("v")
        assertTrue(v.foregrounds.isEmpty() && v.defaultForeground == null && v.levels.isEmpty())
        assertEquals("material-dark", v.schemeFamily)
        assertSame(v, v.atLevel("original"))
        assertTrue(old.groups.schemeForegroundRoles.isEmpty() && old.groups.uiForegroundKeys.isEmpty() && old.groups.highUiContrast.isEmpty() && old.groups.accentUiKeys.isEmpty())
    }

    @Test
    fun unknownTextContrastFollowsTheDefault() {
        val state = GruvboxState()
        state.textContrasts["material"] = "bogus"
        assertNull(state.textContrast(dark))
        assertEquals(dark.atLevel(null).roles, dark.atLevel(state.textContrast(dark)).roles)
        state.setTextContrast(dark, "original")
        assertEquals("original", state.textContrast(dark))
        state.setTextContrast(dark, null)
        assertNull(state.textContrasts["material"])
    }

    @Test
    fun textContrastIsKeptPerPaletteFamily() {
        val other = dark.copy(id = "variant-other", paletteFamily = "other", foregrounds = dark.foregrounds + ("tuned" to dark.foregrounds.getValue("original")))
        val state = GruvboxState()
        state.setTextContrast(dark, "original")
        state.setTextContrast(other, "tuned")
        assertEquals("original", state.textContrast(dark))
        assertEquals("tuned", state.textContrast(other))
        // Same family as dark, but the fixture's light variant has no "original" level.
        assertNull(state.textContrast(fixture.variants.getValue("variant-light")))
        assertEquals(mapOf("material" to "original", "other" to "tuned"), state.textContrasts.toMap())
    }

    @Test
    fun boldAndItalicFollowTheFamilyUntilSet() {
        val state = GruvboxState()
        assertEquals(listOf(false, false), listOf(state.isBold(material, shipped.groups), state.isItalic(material, shipped.groups)))
        assertEquals(listOf(true, true), listOf(state.isBold(baby, shipped.groups), state.isItalic(baby, shipped.groups)))
        state.setItalic(baby, shipped.groups, false)
        state.setBold(material, shipped.groups, true)
        assertEquals(listOf(true, false), listOf(state.isBold(baby, shipped.groups), state.isItalic(baby, shipped.groups)))
        assertEquals(listOf(true, false), listOf(state.isBold(material, shipped.groups), state.isItalic(material, shipped.groups)))
        // Back to the family's own choice leaves the entry unset.
        state.setItalic(baby, shipped.groups, true)
        state.setBold(material, shipped.groups, false)
        assertTrue(state.bold.isEmpty() && state.italic.isEmpty())
    }

    @Test
    fun boldAndItalicSurviveSerialization() {
        val state = GruvboxState()
        state.setBold(baby, shipped.groups, false)
        state.setItalic(material, shipped.groups, true)
        state.setAccent(baby, "red")
        val restored = XmlSerializer.deserialize(XmlSerializer.serialize(state), GruvboxState::class.java)
        assertEquals(listOf(false, true), listOf(restored.isBold(baby, shipped.groups), restored.isItalic(baby, shipped.groups)))
        assertEquals(listOf(false, true), listOf(restored.isBold(material, shipped.groups), restored.isItalic(material, shipped.groups)))
        assertEquals(listOf("aqua", "red"), listOf(restored.accent(material), restored.accent(baby)))
    }

    @Test
    fun turningBoldAndItalicOffStripsBabysStyles() {
        val styles = shipped.groups.styles.getValue(baby.schemeFamily)
        val original = shippedStyles(styles)
        val plain = attributeOverrides(original, shipped.groups, baby, baby, Readability(), KeywordChoice(), bold = false, italic = false)
        assertEquals(original.keys, plain.keys)
        assertTrue(plain.values.all { it.fontType == Font.PLAIN })
        assertEquals(original.mapValues { it.value.foregroundColor }, plain.mapValues { it.value.foregroundColor })
        assertTrue(attributeOverrides(original, shipped.groups, baby, baby, Readability(), KeywordChoice()).isEmpty())
    }

    @Test
    fun turningBoldAndItalicOnAddsMaterialsStyles() {
        val styles = shipped.groups.styles.getValue(material.schemeFamily)
        val keys = styles.bold + styles.italic
        val original = keys.associateWith { TextAttributes().apply { foregroundColor = Color(0xa9b665) } }
        val styled = attributeOverrides(original, shipped.groups, material, material, Readability(), KeywordChoice(), bold = true, italic = true)
        for (key in keys) {
            val expected = (if (key in styles.bold) Font.BOLD else 0) or (if (key in styles.italic) Font.ITALIC else 0)
            assertEquals(key, expected, styled.getValue(key).fontType)
        }
        assertTrue("PY.SELF_PARAMETER" in styles.italic && "DEFAULT_PREDEFINED_SYMBOL" in styles.italic && "DEFAULT_LINE_COMMENT" !in styles.italic)
        assertTrue(attributeOverrides(original, shipped.groups, material, material, Readability(), KeywordChoice(), bold = false, italic = false).isEmpty())
    }

    @Test
    fun italicCommentsStillApplyAfterItalicIsOff() {
        val original = shippedStyles(shipped.groups.styles.getValue(baby.schemeFamily))
        val result = attributeOverrides(original, shipped.groups, baby, baby, Readability(italicComments = true), KeywordChoice(), italic = false)
        assertEquals(Font.ITALIC, result.getValue("DEFAULT_LINE_COMMENT").fontType)
        assertEquals(Font.PLAIN, result.getValue("DEFAULT_KEYWORD").fontType)
        assertEquals(Font.BOLD, (result["DEFAULT_FUNCTION_CALL"] ?: original.getValue("DEFAULT_FUNCTION_CALL")).fontType)
    }

    @Test
    fun accentIsKeptPerPaletteFamily() {
        val state = GruvboxState()
        assertEquals(listOf("aqua", "blue"), listOf(state.accent(material), state.accent(baby)))
        state.accent = "green"
        assertEquals(listOf("green", "blue"), listOf(state.accent(material), state.accent(baby)))
        state.setAccent(baby, "red")
        state.accents["material"] = "orange"
        assertEquals(listOf("orange", "red"), listOf(state.accent(material), state.accent(baby)))
        state.setAccent(baby, "tan")
        assertEquals("blue", state.accent(baby))
    }

    @Test
    fun babyAccentRecolorsFromBlue() {
        val defaults = UIManager.getLookAndFeelDefaults()
        val key = shipped.groups.accentUiKeys.getValue(baby.schemeFamily).first { !it.startsWith("*.") }
        val previous = defaults[key]
        defaults[key] = baby.roles.getValue("blue")
        val overrides = UiOverrides()
        overrides.apply(baby, null, shipped.groups, "green", TabStyle.UNDERLINE)
        assertEquals(baby.roles.getValue("green").rgb, (defaults[key] as Color).rgb)
        overrides.restore()
        defaults[key] = previous
    }

    @Test
    fun babyIndentRainbowUsesBlueForTan() {
        val colors = listOf("orange", "yellow", "green", "aqua", "blue", "purple").map { baby.roles.getValue(it) }
        assertEquals(indentRainbowPalette(colors), indentRainbowPalette(baby))
    }

    @Test
    fun defaultTextContrastIsANoOp() {
        for (level in listOf(null, "material")) {
            assertTrue(attributeOverrides(original, fixture.groups, dark.atLevel(null), dark.atLevel(level), Readability(), KeywordChoice()).isEmpty())
            assertTrue(colorOverrides(schemeColors, fixture.groups, dark.atLevel(null), dark.atLevel(level), highUiContrast = false).isEmpty())
        }
    }

    @Test
    fun textContrastMovesOnlyTheRoleColours() {
        val swapped = attributeOverrides(original, fixture.groups, dark.atLevel(null), dark.atLevel("original"), Readability(), KeywordChoice())
        // Operators and tan keep their colour across levels; the call is green, not fg0, so it stays.
        assertEquals(setOf("DEFAULT_PARAMETER", "DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT", "DEFAULT_DOC_MARKUP"), swapped.keys)
        assertEquals(Color(0xebdbb2), swapped.getValue("DEFAULT_PARAMETER").foregroundColor)
        assertEquals(Color(0xbdae93), swapped.getValue("DEFAULT_LINE_COMMENT").foregroundColor)
        val markup = swapped.getValue("DEFAULT_DOC_MARKUP")
        assertEquals(Color(0xc4a67e), markup.foregroundColor)
        assertEquals(Color(0x8ec07c), markup.effectColor)
        assertEquals(EffectType.LINE_UNDERSCORE, markup.effectType)
        assertEquals(Color(0x89b482), original.getValue("DEFAULT_DOC_MARKUP").effectColor)

        val colors = colorOverrides(schemeColors, fixture.groups, dark.atLevel(null), dark.atLevel("original"), highUiContrast = false)
        assertEquals(mapOf("CARET_COLOR" to Color(0xebdbb2), "LINE_NUMBERS_COLOR" to Color(0x9d8f7f)), colors)
    }

    @Test
    fun readabilityComposesOnTopOfTheLevel() {
        val level = dark.atLevel("original")
        val readable = attributeOverrides(original, fixture.groups, dark.atLevel(null), level, Readability(softenDocs = true, italicParameters = true), KeywordChoice("orange"))
        val parameter = readable.getValue("DEFAULT_PARAMETER")
        assertEquals(Color(0xebdbb2), parameter.foregroundColor)
        assertEquals(Font.ITALIC, parameter.fontType)
        // Docs take the swapped comment colour, and the keyword the level's table.
        assertEquals(Color(0xbdae93), readable.getValue("DEFAULT_DOC_COMMENT_TAG").foregroundColor)
        assertEquals(Color(0xbdae93), readable.getValue("DEFAULT_DOC_MARKUP").foregroundColor)
        assertEquals(Color(0x8ec07c), readable.getValue("DEFAULT_DOC_MARKUP").effectColor)
        assertEquals(Color(0xd99f73), readable.getValue("DEFAULT_KEYWORD").foregroundColor)

        val dimmed = attributeOverrides(original, fixture.groups, dark.atLevel(null), level, Readability(dimComments = true), KeywordChoice())
        assertEquals(Color(0x9d8f7f), dimmed.getValue("DEFAULT_LINE_COMMENT").foregroundColor)
    }

    @Test
    fun highUiContrastRaisesItsKeysAtEveryLevel() {
        val base = dark.atLevel(null)
        assertEquals(
            mapOf("LINE_NUMBERS_COLOR" to Color(0xa89984), "INDENT_GUIDE" to Color(0x5a524c)),
            colorOverrides(schemeColors, fixture.groups, base, base, highUiContrast = true),
        )
        val raised = colorOverrides(schemeColors, fixture.groups, base, dark.atLevel("original"), highUiContrast = true)
        assertEquals(Color(0xbdae93), raised["LINE_NUMBERS_COLOR"])
        assertEquals(Color(0xebdbb2), raised["CARET_COLOR"])
        // Keys the scheme does not define stay inherited.
        assertEquals(setOf("LINE_NUMBERS_COLOR"), colorOverrides(mapOf("LINE_NUMBERS_COLOR" to Color(0x928374)), fixture.groups, base, base, highUiContrast = true).keys)
        // A colour the user changed is theirs.
        assertTrue(colorOverrides(mapOf("INDENT_GUIDE" to Color(0x123456)), fixture.groups, base, base, highUiContrast = true).isEmpty())
    }

    @Test
    fun restoreBringsBackTheExactColours() {
        val storedColors = schemeColors.mapKeys { ColorKey.find(it.key) }.toMutableMap()
        val before = storedColors.toMap()
        val scheme = fakeScheme(original.mapKeys { TextAttributesKey.find(it.key) }.toMutableMap(), storedColors)
        val overrides = SchemeOverrides()
        overrides.applyColors(scheme, colorOverrides(schemeColors, fixture.groups, dark.atLevel(null), dark.atLevel("original"), highUiContrast = false))
        overrides.applyColors(scheme, colorOverrides(schemeColors, fixture.groups, dark.atLevel(null), dark.atLevel(null), highUiContrast = true))
        assertTrue(!overrides.isEmpty)
        assertEquals(Color(0xebdbb2), storedColors[ColorKey.find("CARET_COLOR")])
        assertEquals(Color(0x5a524c), storedColors[ColorKey.find("INDENT_GUIDE")])

        overrides.restore()
        assertTrue(overrides.isEmpty)
        for ((key, color) in before) assertSame(key.externalName, color, storedColors[key])
    }

    @Test
    fun uiTextContrastAndAccentRestoreEverything() {
        val defaults = UIManager.getLookAndFeelDefaults()
        val keys = listOf("Label.foreground", "Component.focusColor", "Fixture.underlineColor")
        val previous = keys.associateWith { defaults[it] }
        val label = Color(0xd4be98)
        val focus = Color(0x89b482)
        val underline = Color(0x8089b482.toInt(), true)
        defaults["Label.foreground"] = label
        defaults["Component.focusColor"] = focus
        defaults["Fixture.underlineColor"] = underline
        val overrides = UiOverrides()
        overrides.apply(dark, "original", fixture.groups, "orange", TabStyle.UNDERLINE)
        assertEquals(0xebdbb2, (defaults["Label.foreground"] as Color).rgb and 0xffffff)
        assertEquals(Color(0xe78a4e), Color((defaults["Component.focusColor"] as Color).rgb))
        assertEquals(Color(0x80e78a4e.toInt(), true), Color((defaults["Fixture.underlineColor"] as Color).rgb, true))

        overrides.restore()
        assertSame(label, defaults["Label.foreground"])
        assertSame(focus, defaults["Component.focusColor"])
        assertSame(underline, defaults["Fixture.underlineColor"])
        for ((key, value) in previous) defaults[key] = value
    }

    private val shipped by lazy { Palette.load() }
    private val material by lazy { shipped.variants.values.first { it.paletteFamily == "material" && it.dark } }
    private val baby by lazy { shipped.variants.values.first { it.paletteFamily == "baby" } }

    /** Attributes carrying [styles]' font bits, as a scheme that ships them defines them. */
    private fun shippedStyles(styles: Styles) = (styles.bold + styles.italic).associateWith { key ->
        TextAttributes().apply {
            foregroundColor = Color(0xfb4934)
            fontType = (if (key in styles.bold) Font.BOLD else 0) or (if (key in styles.italic) Font.ITALIC else 0)
        }
    }

    private val schemeColors = mapOf(
        "CARET_COLOR" to Color(0xd4be98),
        "LINE_NUMBERS_COLOR" to Color(0x928374),
        "INDENT_GUIDE" to Color(0x504945),
    )

    private fun attributes(foreground: String, effect: String? = null) = TextAttributes().apply {
        foregroundColor = Color(foreground.toInt(16))
        if (effect != null) {
            effectColor = Color(effect.toInt(16))
            effectType = EffectType.LINE_UNDERSCORE
        }
    }

    private fun underline() = TextAttributes().apply {
        effectColor = Color(0x928374)
        effectType = EffectType.LINE_UNDERSCORE
    }

    private fun fakeScheme(stored: MutableMap<TextAttributesKey, TextAttributes>, colors: MutableMap<ColorKey, Color> = mutableMapOf()): EditorColorsScheme =
        Proxy.newProxyInstance(javaClass.classLoader, arrayOf(EditorColorsScheme::class.java)) { _, method, args ->
            when (method.name) {
                "getAttributes" -> stored[args[0] as TextAttributesKey]
                "setAttributes" -> stored.put(args[0] as TextAttributesKey, args[1] as TextAttributes).let { null }
                "getColor" -> colors[args[0] as ColorKey]
                "setColor" -> colors.put(args[0] as ColorKey, args[1] as Color).let { null }
                "hashCode" -> 0
                "equals" -> false
                else -> throw UnsupportedOperationException(method.name)
            }
        } as EditorColorsScheme
}
