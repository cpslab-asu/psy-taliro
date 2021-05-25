# Generated from stlParser.g4 by ANTLR 4.5.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .stlParser import stlParser
else:
    from stlParser import stlParser

import tltk_mtl as mtl

# This class defines a complete generic visitor for a parse tree produced by stlParser.
class stlParserVisitor(ParseTreeVisitor):
    def __init__(self, lexer, data, mode):
        self._lexer = lexer
        self._mode = mode

        if type(data) is dict:
            self._predicates = data
        elif type(data) is list:
            self._variables = data
        else:
            raise Exception(
                "data: provided data is not a dict of mtl.Predicate's or list of variable names"
            )

    # Visit a parse tree produced by stlParser#stlSpecification.
    def visitStlSpecification(self, ctx: stlParser.StlSpecificationContext):
        return self.visit(ctx.getRuleContext().getChild(0))

    # Visit a parse tree produced by stlParser#predicateExpr.
    def visitPredicateExpr(self, ctx: stlParser.PredicateExprContext):
        return self.visit(ctx.getRuleContext().getChild(0))

    # Visit a parse tree produced by stlParser#opFutureExpr.
    def visitOpFutureExpr(self, ctx: stlParser.OpFutureExprContext):
        pred = self.visit(ctx.getRuleContext().getChild(2))
        bounds = self.visit(ctx.getRuleContext().getChild(1))

        return mtl.Finally(bounds[0], bounds[1], pred, self._mode)

    # Visit a parse tree produced by stlParser#parenPhiExpr.
    def visitParenPhiExpr(self, ctx: stlParser.ParenPhiExprContext):
        return self.visit(ctx.getRuleContext().getChild(1))

    # Visit a parse tree produced by stlParser#opUntilExpr.
    def visitOpUntilExpr(self, ctx: stlParser.OpUntilExprContext):
        pred1 = self.visit(ctx.getRuleContext().getChild(0))
        pred2 = self.visit(ctx.getRuleContext().getChild(3))

        bounds = self.visit(ctx.getRuleContext().getChild(2))

        return mtl.Until(bounds[0], bounds[1], pred1, pred2, self._mode)

    # Visit a parse tree produced by stlParser#opGloballyExpr.
    def visitOpGloballyExpr(self, ctx: stlParser.OpGloballyExprContext):
        pred = self.visit(ctx.getRuleContext().getChild(2))
        bounds = self.visit(ctx.getRuleContext().getChild(1))

        return mtl.Global(bounds[0], bounds[1], pred, self._mode)

    # Visit a parse tree produced by stlParser#opLogicalExpr.
    def visitOpLogicalExpr(self, ctx: stlParser.OpLogicalExprContext):
        pred1 = self.visit(ctx.getRuleContext().getChild(0))
        pred2 = self.visit(ctx.getRuleContext().getChild(2))

        type = ctx.getRuleContext().getChild(1).getSymbol().type

        if type == self._lexer.ANDOP:
            return mtl.And(pred1, pred2, self._mode)
        elif type == self._lexer.OROP:
            return mtl.Or(pred1, pred2, self._mode)

    # Visit a parse tree produced by stlParser#opReleaseExpr.
    def visitOpReleaseExpr(self, ctx: stlParser.OpReleaseExprContext):
        pred1 = self.visit(ctx.getRuleContext().getChild(0))
        pred2 = self.visit(ctx.getRuleContext().getChild(3))

        bounds = self.visit(ctx.getRuleContext().getChild(2))

        return mtl.Not(mtl.Until(bounds[0], bounds[1], mtl.Not(pred1), mtl.Not(pred2)))

    # Visit a parse tree produced by stlParser#opNextExpr.
    def visitOpNextExpr(self, ctx: stlParser.OpNextExprContext):
        pred = self.visit(ctx.getRuleContext().getChild(1))

        return mtl.Next(pred)

    # Visit a parse tree produced by stlParser#opPropExpr.
    def visitOpPropExpr(self, ctx: stlParser.OpPropExprContext):
        pred1 = self.visit(ctx.getRuleContext().getChild(0))
        pred2 = self.visit(ctx.getRuleContext().getChild(2))

        return mtl.Or(mtl.Not(pred1), pred2, self._mode)

    # Visit a parse tree produced by stlParser#opNegExpr.
    def visitOpNegExpr(self, ctx: stlParser.OpNegExprContext):
        pred = self.visit(ctx.getRuleContext().getChild(1))

        return mtl.Not(pred, self._mode)

    # Visit a parse tree produced by stlParser#predicate.
    def visitPredicate(self, ctx: stlParser.PredicateContext):
        child_count = ctx.getRuleContext().getChildCount()

        if child_count == 1:
            # the predicate name only exists, so return the relevant
            # mtl.Predicate data structure

            return self._predicates[ctx.getRuleContext().getChild(0).getText()]
        else:
            minus = ctx.getRuleContext().getChild(0).getText()

            if minus == "-":
                var = ctx.getRuleContext().getChild(1).getText()
                operator = ctx.getRuleContext().getChild(2).getText()
                value = ctx.getRuleContext().getChild(3).getText()
            else:
                var = ctx.getRuleContext().getChild(0).getText()
                operator = ctx.getRuleContext().getChild(1).getText()
                value = ctx.getRuleContext().getChild(2).getText()

            value = float(value)

            # check that the variable is valid
            if var not in self._variables:
                raise Exception(
                    "predicate: " + var + " is not in the list of valid variables"
                )

            if operator == "<" or operator == ">":
                raise Exception(
                    "Warning: strict relational operator used. Please use non-strict (<= or >=)"
                )
            elif operator == "<=":
                if minus == "-":
                    return mtl.Predicate(var, -1, value)
                else:
                    return mtl.Predicate(var, 1, value)
            elif operator == ">=":
                if minus == "-":
                    return mtl.Predicate(var, 1, -value)
                else:
                    return mtl.Predicate(var, -1, -value)

    # Visit a parse tree produced by stlParser#interval.
    def visitInterval(self, ctx: stlParser.IntervalContext):
        bounds = []
        bounds.append(float(ctx.getRuleContext().getChild(1).getText()))
        bounds.append(float(ctx.getRuleContext().getChild(3).getText()))

        return bounds


del stlParser
