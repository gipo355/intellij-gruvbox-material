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
        val coupled = readabilityOverrides(original, fixture.groups, dark.roles, Readability(), orange)
        assertEquals(setOf("DEFAULT_OPERATION_SIGN", "DEFAULT_KEYWORD"), coupled.keys)
        assertEquals(Color(0xd4be98), coupled.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)
        assertEquals(orange, coupled.getValue("DEFAULT_KEYWORD").foregroundColor)

        val quiet = readabilityOverrides(original, fixture.groups, dark.roles, Readability(quietOperators = true), orange)
        assertEquals(Color(0xa89984), quiet.getValue("DEFAULT_OPERATION_SIGN").foregroundColor)

        assertTrue(readabilityOverrides(original, fixture.groups, dark.roles, Readability(), keywordColor(dark, KeywordChoice())).isEmpty())
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
