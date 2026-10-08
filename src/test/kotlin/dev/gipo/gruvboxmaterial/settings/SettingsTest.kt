package dev.gipo.gruvboxmaterial.settings

import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.markup.EffectType
import com.intellij.openapi.editor.markup.TextAttributes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.Color
import java.awt.Font
import java.lang.reflect.Proxy

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
        assertEquals(listOf("Component.focusColor", "*.underlineColor"), fixture.groups.accentUiKeys)
    }

    @Test
    fun shippedPaletteCoversEveryRoleTheFeaturesRead() {
        val shipped = Palette.load()
        val roles = listOf("fg0", "grey1", "grey2", "bg3", "bg_current_word") + ACCENTS
        val missing = shipped.variants.values.flatMap { v -> roles.filter { it !in v.roles }.map { "${v.id}: $it" } }
        assertTrue("missing roles: $missing", missing.isEmpty())
        assertTrue(shipped.groups.operators.isNotEmpty() && shipped.groups.comments.isNotEmpty() && shipped.groups.accentUiKeys.isNotEmpty())
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
    fun keywordFamilyMovesOperatorsToForegroundUnlessQuiet() {
        val orange = Color(0xcd936a)
        val coupled = readabilityOverrides(original, fixture.groups, dark.roles, Readability(), orange, "orange")
        assertEquals(setOf("DEFAULT_OPERATION_SIGN", "DEFAULT_KEYWORD"), coupled.keys)
        assertEquals(Color(0xd4be98), coupled.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        assertEquals(orange, coupled.getValue("DEFAULT_KEYWORD").foregroundColor)

        val quiet = readabilityOverrides(original, fixture.groups, dark.roles, Readability(quietOperators = true), orange, "orange")
        assertEquals(Color(0xa89984), quiet.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)

        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability(), keywordColor(dark, KeywordChoice())).isEmpty())
    }

    @Test
    fun onlyClashingKeywordFamiliesMoveOperators() {
        val color = Color(0xb0a090)
        for (family in listOf("red", "orange", "clay")) {
            val overrides = readabilityOverrides(original, fixture.groups, dark.roles, Readability(), color, family)
            assertEquals(family, Color(0xd4be98), overrides.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        }
        for (family in listOf("stone", "slate", PLAIN)) {
            val overrides = readabilityOverrides(original, fixture.groups, dark.roles, Readability(), color, family)
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

    private fun fakeScheme(stored: MutableMap<TextAttributesKey, TextAttributes>): EditorColorsScheme =
        Proxy.newProxyInstance(javaClass.classLoader, arrayOf(EditorColorsScheme::class.java)) { _, method, args ->
            when (method.name) {
                "getAttributes" -> stored[args[0] as TextAttributesKey]
                "setAttributes" -> stored.put(args[0] as TextAttributesKey, args[1] as TextAttributes).let { null }
                "hashCode" -> 0
                "equals" -> false
                else -> throw UnsupportedOperationException(method.name)
            }
        } as EditorColorsScheme
}
