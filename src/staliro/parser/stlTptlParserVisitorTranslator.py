# Generated from stlParser.g4 by ANTLR 4.5.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .stlParser import stlParser
else:
    from stlParser import stlParser


class stlTptlParserVisitorTranslator(ParseTreeVisitor):
    """Traverse the generated ANTLR parse tree and translate STL to TPTL."""

    def __init__(self, lexer):
        self.lexer = lexer
        self.freeze = 0

    def freezeTime(self, freeze, lower, upper, subformulas, token_type):
        translation = ""
        if token_type == self.lexer.FUTUREOP:
            translation = (
                f"@Var_t{freeze} <>"
                f"(({{ Var_t{freeze} >= {str(lower)} }} /\\ {{ Var_t{freeze} <= {str(upper)} }}) "
                f"/\\ {subformulas[0]})"
            )
        elif token_type == self.lexer.GLOBALLYOP:
            translation = (
                f"@Var_t{freeze} []"
                f"(({{ Var_t{freeze} >= {str(lower)} }} /\\ {{ Var_t{freeze} <= {str(upper)} }}) "
                f"-> {subformulas[0]})"
            )
        elif token_type == self.lexer.NEXTOP:
            translation = (
                f"@Var_t{freeze} X"
                f"(({{ Var_t{freeze} >= {str(lower)} }} /\\ {{ Var_t{freeze} <= {str(upper)} }}) "
                f"/\\ {subformulas[0]})"
            )
        elif token_type == self.lexer.UNTILOP:
            translation = (
                f"@Var_t{freeze} ( {subformulas[0]} U "
                f"(({{ Var_t{freeze} >= {str(lower)} }} /\\ {{ Var_t{freeze} <= {str(upper)} }}) "
                f"/\\ {subformulas[1]}))"
            )
        elif token_type == self.lexer.RELEASEOP:
            translation = (
                f"!(@Var_t{freeze} (!{subformulas[0]} U "
                f"(({{ Var_t{freeze} >= {str(lower)} }} /\\ {{ Var_t{freeze} <= {str(upper)} }}) "
                f"/\\ !{subformulas[1]})))"
            )

        return translation

    # Visit a parse tree produced by stlParser#stlSpecification.
    def visitStlSpecification(self, ctx: stlParser.StlSpecificationContext) -> str:
        return self.visit(ctx.getRuleContext().getChild(0))

    # Visit a parse tree produced by stlParser#predicateExpr.
    def visitPredicateExpr(self, ctx: stlParser.PredicateExprContext) -> str:
        return self.visit(ctx.getRuleContext().getChild(0))

    # Visit a parse tree produced by stlParser#opFutureExpr.
    def visitOpFutureExpr(self, ctx: stlParser.OpFutureExprContext) -> str:
        child_count = ctx.getRuleContext().getChildCount()

        phi = ""
        if child_count == 3:
            index = self.freeze
            self.freeze += 1

            bounds = self.visit(ctx.getRuleContext().getChild(1))
            phi = self.visit(ctx.getRuleContext().getChild(2))
            token_type = ctx.getRuleContext().getChild(0).getSymbol().type

            return self.freezeTime(index, bounds[0], bounds[1], [phi], token_type)
        else:
            phi = self.visit(ctx.getRuleContext().getChild(1))
            return "<> " + phi

    # Visit a parse tree produced by stlParser#parenPhiExpr.
    def visitParenPhiExpr(self, ctx: stlParser.ParenPhiExprContext) -> str:
        return "( " + self.visit(ctx.getRuleContext().getChild(1)) + " )"

    # Visit a parse tree produced by stlParser#opUntilExpr.
    def visitOpUntilExpr(self, ctx: stlParser.OpUntilExprContext) -> str:
        child_count = ctx.getRuleContext().getChildCount()

        phi_1 = ""
        phi_2 = ""

        if child_count == 4:
            index = self.freeze
            self.freeze += 1

            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(3))

            bounds = self.visit(ctx.getRuleContext().getChild(2))
            token_type = ctx.getRuleContext().getChild(1).getSymbol().type

            return self.freezeTime(index, bounds[0], bounds[1], [phi_1, phi_2], token_type)
        else:
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + " U " + phi_2

    # Visit a parse tree produced by stlParser#opGloballyExpr.
    def visitOpGloballyExpr(self, ctx: stlParser.OpGloballyExprContext) -> str:
        child_count = ctx.getRuleContext().getChildCount()

        phi = ""
        if child_count == 3:
            index = self.freeze
            self.freeze += 1

            bounds = self.visit(ctx.getRuleContext().getChild(1))
            phi = self.visit(ctx.getRuleContext().getChild(2))
            token_type = ctx.getRuleContext().getChild(0).getSymbol().type

            return self.freezeTime(index, bounds[0], bounds[1], [phi], token_type)
        else:
            phi = self.visit(ctx.getRuleContext().getChild(1))
            return "[] " + phi

    # Visit a parse tree produced by stlParser#opLogicalExpr.
    def visitOpLogicalExpr(self, ctx: stlParser.OpLogicalExprContext) -> str:
        token_type = ctx.getRuleContext().getChild(1).getSymbol().type

        phi_1 = ""
        phi_2 = ""

        if token_type == self.lexer.ANDOP:
            # conjunction
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + r" /\ " + phi_2
        elif token_type == self.lexer.OROP:
            # disjunction
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + r" \/ " + phi_2

    # Visit a parse tree produced by stlParser#opReleaseExpr.
    def visitOpReleaseExpr(self, ctx: stlParser.OpReleaseExprContext) -> str:
        child_count = ctx.getRuleContext().getChildCount()

        phi_1 = ""
        phi_2 = ""

        if child_count == 4:
            index = self.freeze
            self.freeze += 1

            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(3))

            bounds = self.visit(ctx.getRuleContext().getChild(2))
            token_type = ctx.getRuleContext().getChild(1).getSymbol().type

            return self.freezeTime(index, bounds[0], bounds[1], [phi_1, phi_2], token_type)
        else:
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + " R " + phi_2

    # Visit a parse tree produced by stlParser#opNextExpr.
    def visitOpNextExpr(self, ctx: stlParser.OpNextExprContext) -> str:
        child_count = ctx.getRuleContext().getChildCount()

        phi = ""
        if child_count == 3:
            index = self.freeze
            self.freeze += 1

            bounds = self.visit(ctx.getRuleContext().getChild(1))
            phi = self.visit(ctx.getRuleContext().getChild(2))
            token_type = ctx.getRuleContext().getChild(0).getSymbol().type

            return self.freezeTime(index, bounds[0], bounds[1], [phi], token_type)
        else:
            phi = self.visit(ctx.getRuleContext().getChild(1))
            return "X " + phi

    # Visit a parse tree produced by stlParser#opPropExpr.
    def visitOpPropExpr(self, ctx: stlParser.OpPropExprContext) -> str:
        token_type = ctx.getRuleContext().getChild(1).getSymbol().type

        phi_1 = ""
        phi_2 = ""

        if token_type == self.lexer.IMPLIESOP:
            # implication
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + " -> " + phi_2
        elif token_type == self.lexer.EQUIVOP:
            # equivalency
            phi_1 = self.visit(ctx.getRuleContext().getChild(0))
            phi_2 = self.visit(ctx.getRuleContext().getChild(2))

            return phi_1 + " <-> " + phi_2

    # Visit a parse tree produced by stlParser#opNegExpr.
    def visitOpNegExpr(self, ctx: stlParser.OpNegExprContext) -> str:
        return "! " + self.visit(ctx.getRuleContext().getChild(1))

    # Visit a parse tree produced by stlParser#predicate.
    def visitPredicate(self, ctx: stlParser.PredicateContext) -> str:
        return ctx.getRuleContext().getChild(0).getText()

    # Visit a parse tree produced by stlParser#interval.
    def visitInterval(self, ctx: stlParser.IntervalContext) -> str:
        bounds = []
        bounds.append(float(ctx.getRuleContext().getChild(1).getText()))
        bounds.append(float(ctx.getRuleContext().getChild(3).getText()))

        return bounds


del stlParser
