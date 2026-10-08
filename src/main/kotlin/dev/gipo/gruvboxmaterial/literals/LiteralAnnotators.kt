package dev.gipo.gruvboxmaterial.literals

import com.intellij.lang.annotation.AnnotationHolder
import com.intellij.lang.annotation.Annotator
import com.intellij.lang.annotation.HighlightSeverity
import com.intellij.lang.javascript.JSTokenTypes
import com.intellij.lang.javascript.psi.JSReferenceExpression
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors
import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.options.Scheme
import com.intellij.psi.JavaTokenType
import com.intellij.psi.PsiElement
import com.intellij.psi.tree.IElementType
import com.intellij.psi.tree.TokenSet
import com.intellij.psi.util.elementType
import dev.gipo.gruvboxmaterial.settings.GruvboxService
import org.jetbrains.kotlin.lexer.KtTokens

/**
 * Paints null / true / false (and undefined) with the predefined-symbol purple: the languages lex them as keywords, so
 * the scheme alone cannot separate them from `if` or `return`. Leaf tokens only, no resolve, and only under our schemes.
 */
abstract class LiteralAnnotator : Annotator {
    protected abstract fun isLiteral(element: PsiElement, type: IElementType): Boolean

    override fun annotate(element: PsiElement, holder: AnnotationHolder) {
        if (element.firstChild != null) return
        val type = element.elementType ?: return
        if (!isLiteral(element, type) || !ourSchemeActive()) return
        holder.newSilentAnnotation(HighlightSeverity.INFORMATION).textAttributes(DefaultLanguageHighlighterColors.PREDEFINED_SYMBOL).create()
    }

    private fun ourSchemeActive(): Boolean {
        val name = EditorColorsManager.getInstance().globalScheme.name.removePrefix(Scheme.EDITABLE_COPY_PREFIX)
        return GruvboxService.getInstance().palette.variantForScheme(name) != null
    }
}

class JavaLiteralAnnotator : LiteralAnnotator() {
    private val literals = TokenSet.create(JavaTokenType.NULL_KEYWORD, JavaTokenType.TRUE_KEYWORD, JavaTokenType.FALSE_KEYWORD)
    override fun isLiteral(element: PsiElement, type: IElementType) = type in literals
}

class KotlinLiteralAnnotator : LiteralAnnotator() {
    private val literals = TokenSet.create(KtTokens.NULL_KEYWORD, KtTokens.TRUE_KEYWORD, KtTokens.FALSE_KEYWORD)
    override fun isLiteral(element: PsiElement, type: IElementType) = type in literals
}

class JavaScriptLiteralAnnotator : LiteralAnnotator() {
    private val literals = TokenSet.create(JSTokenTypes.NULL_KEYWORD, JSTokenTypes.TRUE_KEYWORD, JSTokenTypes.FALSE_KEYWORD)

    // UNDEFINED_KEYWORD also names parameters, variables and shorthand destructuring keys: only an unqualified
    // reference is the value. Member names (`a.undefined`, `{undefined: 1}`, enum members) lex as IDENTIFIER.
    override fun isLiteral(element: PsiElement, type: IElementType) = type in literals ||
        type == JSTokenTypes.UNDEFINED_KEYWORD &&
        (element.parent as? JSReferenceExpression)?.let { it.qualifier == null } == true
}
