# Generated from stlParser.g4 by ANTLR 4.5.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .stlParser import stlParser
else:
    from stlParser import stlParser

# This class defines a complete generic visitor for a parse tree produced by stlParser.

class stlParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by stlParser#stlSpecification.
    def visitStlSpecification(self, ctx:stlParser.StlSpecificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#predicateExpr.
    def visitPredicateExpr(self, ctx:stlParser.PredicateExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opFutureExpr.
    def visitOpFutureExpr(self, ctx:stlParser.OpFutureExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#parenPhiExpr.
    def visitParenPhiExpr(self, ctx:stlParser.ParenPhiExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opUntilExpr.
    def visitOpUntilExpr(self, ctx:stlParser.OpUntilExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opGloballyExpr.
    def visitOpGloballyExpr(self, ctx:stlParser.OpGloballyExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opLogicalExpr.
    def visitOpLogicalExpr(self, ctx:stlParser.OpLogicalExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opReleaseExpr.
    def visitOpReleaseExpr(self, ctx:stlParser.OpReleaseExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opNextExpr.
    def visitOpNextExpr(self, ctx:stlParser.OpNextExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opPropExpr.
    def visitOpPropExpr(self, ctx:stlParser.OpPropExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#opNegExpr.
    def visitOpNegExpr(self, ctx:stlParser.OpNegExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#predicate.
    def visitPredicate(self, ctx:stlParser.PredicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by stlParser#interval.
    def visitInterval(self, ctx:stlParser.IntervalContext):
        return self.visitChildren(ctx)



del stlParser