# Generated from stlParser.g4 by ANTLR 4.5.3
# encoding: utf-8
from antlr4 import *
from io import StringIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\3\32")
        buf.write("M\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\3\2\3\2\3\2\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\5\3\27\n\3\3\3\3\3\3\3\5")
        buf.write("\3\34\n\3\3\3\3\3\3\3\5\3!\n\3\3\3\3\3\5\3%\n\3\3\3\3")
        buf.write("\3\3\3\5\3*\n\3\3\3\3\3\3\3\3\3\5\3\60\n\3\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\7\39\n\3\f\3\16\3<\13\3\3\4\5\4?\n\4")
        buf.write("\3\4\3\4\3\4\3\4\5\4E\n\4\3\5\3\5\3\5\3\5\3\5\3\5\3\5")
        buf.write("\2\3\4\6\2\4\6\b\2\7\3\2\22\23\3\2\24\25\4\2\4\4\6\6\4")
        buf.write("\2\26\26\30\30\4\2\5\5\7\7X\2\n\3\2\2\2\4$\3\2\2\2\6D")
        buf.write("\3\2\2\2\bF\3\2\2\2\n\13\5\4\3\2\13\f\7\2\2\3\f\3\3\2")
        buf.write("\2\2\r\16\b\3\1\2\16\17\7\4\2\2\17\20\5\4\3\2\20\21\7")
        buf.write("\5\2\2\21%\3\2\2\2\22\23\7\n\2\2\23%\5\4\3\13\24\26\7")
        buf.write("\r\2\2\25\27\5\b\5\2\26\25\3\2\2\2\26\27\3\2\2\2\27\30")
        buf.write("\3\2\2\2\30%\5\4\3\n\31\33\7\16\2\2\32\34\5\b\5\2\33\32")
        buf.write("\3\2\2\2\33\34\3\2\2\2\34\35\3\2\2\2\35%\5\4\3\t\36 \7")
        buf.write('\17\2\2\37!\5\b\5\2 \37\3\2\2\2 !\3\2\2\2!"\3\2\2\2"')
        buf.write("%\5\4\3\b#%\5\6\4\2$\r\3\2\2\2$\22\3\2\2\2$\24\3\2\2\2")
        buf.write("$\31\3\2\2\2$\36\3\2\2\2$#\3\2\2\2%:\3\2\2\2&'\f\7\2")
        buf.write("\2')\7\20\2\2(*\5\b\5\2)(\3\2\2\2)*\3\2\2\2*+\3\2\2\2")
        buf.write("+9\5\4\3\b,-\f\6\2\2-/\7\21\2\2.\60\5\b\5\2/.\3\2\2\2")
        buf.write("/\60\3\2\2\2\60\61\3\2\2\2\619\5\4\3\7\62\63\f\5\2\2\63")
        buf.write("\64\t\2\2\2\649\5\4\3\6\65\66\f\4\2\2\66\67\t\3\2\2\67")
        buf.write("9\5\4\3\58&\3\2\2\28,\3\2\2\28\62\3\2\2\28\65\3\2\2\2")
        buf.write("9<\3\2\2\2:8\3\2\2\2:;\3\2\2\2;\5\3\2\2\2<:\3\2\2\2=?")
        buf.write("\7\t\2\2>=\3\2\2\2>?\3\2\2\2?@\3\2\2\2@A\7\27\2\2AB\7")
        buf.write("\13\2\2BE\7\30\2\2CE\7\27\2\2D>\3\2\2\2DC\3\2\2\2E\7\3")
        buf.write("\2\2\2FG\t\4\2\2GH\t\5\2\2HI\7\b\2\2IJ\t\5\2\2JK\t\6\2")
        buf.write("\2K\t\3\2\2\2\f\26\33 $)/8:>D")
        return buf.getvalue()


class stlParser(Parser):

    grammarFileName = "stlParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [DFA(ds, i) for i, ds in enumerate(atn.decisionToState)]

    sharedContextCache = PredictionContextCache()

    literalNames = [
        "<INVALID>",
        "<INVALID>",
        "'('",
        "')'",
        "'['",
        "']'",
        "','",
        "'-'",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "'inf'",
    ]

    symbolicNames = [
        "<INVALID>",
        "WS",
        "LPAREN",
        "RPAREN",
        "LBRACK",
        "RBRACK",
        "COMMA",
        "MINUS",
        "NEGATION",
        "RELOP",
        "EQUALITYOP",
        "NEXTOP",
        "FUTUREOP",
        "GLOBALLYOP",
        "UNTILOP",
        "RELEASEOP",
        "ANDOP",
        "OROP",
        "IMPLIESOP",
        "EQUIVOP",
        "INF",
        "NAME",
        "NUMBER",
        "INT_NUMBER",
        "FLOAT_NUMBER",
    ]

    RULE_stlSpecification = 0
    RULE_phi = 1
    RULE_predicate = 2
    RULE_interval = 3

    ruleNames = ["stlSpecification", "phi", "predicate", "interval"]

    EOF = Token.EOF
    WS = 1
    LPAREN = 2
    RPAREN = 3
    LBRACK = 4
    RBRACK = 5
    COMMA = 6
    MINUS = 7
    NEGATION = 8
    RELOP = 9
    EQUALITYOP = 10
    NEXTOP = 11
    FUTUREOP = 12
    GLOBALLYOP = 13
    UNTILOP = 14
    RELEASEOP = 15
    ANDOP = 16
    OROP = 17
    IMPLIESOP = 18
    EQUIVOP = 19
    INF = 20
    NAME = 21
    NUMBER = 22
    INT_NUMBER = 23
    FLOAT_NUMBER = 24

    def __init__(self, input: TokenStream):
        super().__init__(input)
        self.checkVersion("4.5.3")
        self._interp = ParserATNSimulator(
            self, self.atn, self.decisionsToDFA, self.sharedContextCache
        )
        self._predicates = None

    class StlSpecificationContext(ParserRuleContext):
        def __init__(self, parser, parent: ParserRuleContext = None, invokingState: int = -1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def EOF(self):
            return self.getToken(stlParser.EOF, 0)

        def getRuleIndex(self):
            return stlParser.RULE_stlSpecification

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterStlSpecification"):
                listener.enterStlSpecification(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitStlSpecification"):
                listener.exitStlSpecification(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitStlSpecification"):
                return visitor.visitStlSpecification(self)
            else:
                return visitor.visitChildren(self)

    def stlSpecification(self):

        localctx = stlParser.StlSpecificationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_stlSpecification)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 8
            self.phi(0)
            self.state = 9
            self.match(stlParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class PhiContext(ParserRuleContext):
        def __init__(self, parser, parent: ParserRuleContext = None, invokingState: int = -1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def getRuleIndex(self):
            return stlParser.RULE_phi

        def copyFrom(self, ctx: ParserRuleContext):
            super().copyFrom(ctx)

    class PredicateExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def predicate(self):
            return self.getTypedRuleContext(stlParser.PredicateContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterPredicateExpr"):
                listener.enterPredicateExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitPredicateExpr"):
                listener.exitPredicateExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitPredicateExpr"):
                return visitor.visitPredicateExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpFutureExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FUTUREOP(self):
            return self.getToken(stlParser.FUTUREOP, 0)

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def interval(self):
            return self.getTypedRuleContext(stlParser.IntervalContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpFutureExpr"):
                listener.enterOpFutureExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpFutureExpr"):
                listener.exitOpFutureExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpFutureExpr"):
                return visitor.visitOpFutureExpr(self)
            else:
                return visitor.visitChildren(self)

    class ParenPhiExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LPAREN(self):
            return self.getToken(stlParser.LPAREN, 0)

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def RPAREN(self):
            return self.getToken(stlParser.RPAREN, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterParenPhiExpr"):
                listener.enterParenPhiExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitParenPhiExpr"):
                listener.exitParenPhiExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitParenPhiExpr"):
                return visitor.visitParenPhiExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpUntilExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def phi(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(stlParser.PhiContext)
            else:
                return self.getTypedRuleContext(stlParser.PhiContext, i)

        def UNTILOP(self):
            return self.getToken(stlParser.UNTILOP, 0)

        def interval(self):
            return self.getTypedRuleContext(stlParser.IntervalContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpUntilExpr"):
                listener.enterOpUntilExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpUntilExpr"):
                listener.exitOpUntilExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpUntilExpr"):
                return visitor.visitOpUntilExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpGloballyExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def GLOBALLYOP(self):
            return self.getToken(stlParser.GLOBALLYOP, 0)

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def interval(self):
            return self.getTypedRuleContext(stlParser.IntervalContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpGloballyExpr"):
                listener.enterOpGloballyExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpGloballyExpr"):
                listener.exitOpGloballyExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpGloballyExpr"):
                return visitor.visitOpGloballyExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpLogicalExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def phi(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(stlParser.PhiContext)
            else:
                return self.getTypedRuleContext(stlParser.PhiContext, i)

        def ANDOP(self):
            return self.getToken(stlParser.ANDOP, 0)

        def OROP(self):
            return self.getToken(stlParser.OROP, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpLogicalExpr"):
                listener.enterOpLogicalExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpLogicalExpr"):
                listener.exitOpLogicalExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpLogicalExpr"):
                return visitor.visitOpLogicalExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpReleaseExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def phi(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(stlParser.PhiContext)
            else:
                return self.getTypedRuleContext(stlParser.PhiContext, i)

        def RELEASEOP(self):
            return self.getToken(stlParser.RELEASEOP, 0)

        def interval(self):
            return self.getTypedRuleContext(stlParser.IntervalContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpReleaseExpr"):
                listener.enterOpReleaseExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpReleaseExpr"):
                listener.exitOpReleaseExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpReleaseExpr"):
                return visitor.visitOpReleaseExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpNextExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NEXTOP(self):
            return self.getToken(stlParser.NEXTOP, 0)

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def interval(self):
            return self.getTypedRuleContext(stlParser.IntervalContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpNextExpr"):
                listener.enterOpNextExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpNextExpr"):
                listener.exitOpNextExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpNextExpr"):
                return visitor.visitOpNextExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpPropExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def phi(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(stlParser.PhiContext)
            else:
                return self.getTypedRuleContext(stlParser.PhiContext, i)

        def IMPLIESOP(self):
            return self.getToken(stlParser.IMPLIESOP, 0)

        def EQUIVOP(self):
            return self.getToken(stlParser.EQUIVOP, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpPropExpr"):
                listener.enterOpPropExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpPropExpr"):
                listener.exitOpPropExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpPropExpr"):
                return visitor.visitOpPropExpr(self)
            else:
                return visitor.visitChildren(self)

    class OpNegExprContext(PhiContext):
        def __init__(self, parser, ctx: ParserRuleContext):  # actually a stlParser.PhiContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NEGATION(self):
            return self.getToken(stlParser.NEGATION, 0)

        def phi(self):
            return self.getTypedRuleContext(stlParser.PhiContext, 0)

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterOpNegExpr"):
                listener.enterOpNegExpr(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitOpNegExpr"):
                listener.exitOpNegExpr(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitOpNegExpr"):
                return visitor.visitOpNegExpr(self)
            else:
                return visitor.visitChildren(self)

    def phi(self, _p: int = 0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = stlParser.PhiContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 2
        self.enterRecursionRule(localctx, 2, self.RULE_phi, _p)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 34
            token = self._input.LA(1)
            if token in [stlParser.LPAREN]:
                localctx = stlParser.ParenPhiExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 12
                self.match(stlParser.LPAREN)
                self.state = 13
                self.phi(0)
                self.state = 14
                self.match(stlParser.RPAREN)

            elif token in [stlParser.NEGATION]:
                localctx = stlParser.OpNegExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 16
                self.match(stlParser.NEGATION)
                self.state = 17
                self.phi(9)

            elif token in [stlParser.NEXTOP]:
                localctx = stlParser.OpNextExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 18
                self.match(stlParser.NEXTOP)
                self.state = 20
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input, 0, self._ctx)
                if la_ == 1:
                    self.state = 19
                    self.interval()

                self.state = 22
                self.phi(8)

            elif token in [stlParser.FUTUREOP]:
                localctx = stlParser.OpFutureExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 23
                self.match(stlParser.FUTUREOP)
                self.state = 25
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input, 1, self._ctx)
                if la_ == 1:
                    self.state = 24
                    self.interval()

                self.state = 27
                self.phi(7)

            elif token in [stlParser.GLOBALLYOP]:
                localctx = stlParser.OpGloballyExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 28
                self.match(stlParser.GLOBALLYOP)
                self.state = 30
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input, 2, self._ctx)
                if la_ == 1:
                    self.state = 29
                    self.interval()

                self.state = 32
                self.phi(6)

            elif token in [stlParser.MINUS, stlParser.NAME]:
                localctx = stlParser.PredicateExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 33
                self.predicate()

            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 56
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input, 7, self._ctx)
            while _alt != 2 and _alt != ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 54
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input, 6, self._ctx)
                    if la_ == 1:
                        localctx = stlParser.OpUntilExprContext(
                            self, stlParser.PhiContext(self, _parentctx, _parentState)
                        )
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_phi)
                        self.state = 36
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException

                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 37
                        self.match(stlParser.UNTILOP)
                        self.state = 39
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input, 4, self._ctx)
                        if la_ == 1:
                            self.state = 38
                            self.interval()

                        self.state = 41
                        self.phi(6)
                        pass

                    elif la_ == 2:
                        localctx = stlParser.OpReleaseExprContext(
                            self, stlParser.PhiContext(self, _parentctx, _parentState)
                        )
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_phi)
                        self.state = 42
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException

                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 43
                        self.match(stlParser.RELEASEOP)
                        self.state = 45
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input, 5, self._ctx)
                        if la_ == 1:
                            self.state = 44
                            self.interval()

                        self.state = 47
                        self.phi(5)
                        pass

                    elif la_ == 3:
                        localctx = stlParser.OpLogicalExprContext(
                            self, stlParser.PhiContext(self, _parentctx, _parentState)
                        )
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_phi)
                        self.state = 48
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException

                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 49
                        _la = self._input.LA(1)
                        if not (_la == stlParser.ANDOP or _la == stlParser.OROP):
                            self._errHandler.recoverInline(self)
                        else:
                            self.consume()
                        self.state = 50
                        self.phi(4)
                        pass

                    elif la_ == 4:
                        localctx = stlParser.OpPropExprContext(
                            self, stlParser.PhiContext(self, _parentctx, _parentState)
                        )
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_phi)
                        self.state = 51
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException

                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 52
                        _la = self._input.LA(1)
                        if not (_la == stlParser.IMPLIESOP or _la == stlParser.EQUIVOP):
                            self._errHandler.recoverInline(self)
                        else:
                            self.consume()
                        self.state = 53
                        self.phi(3)
                        pass

                self.state = 58
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input, 7, self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx

    class PredicateContext(ParserRuleContext):
        def __init__(self, parser, parent: ParserRuleContext = None, invokingState: int = -1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NAME(self):
            return self.getToken(stlParser.NAME, 0)

        def RELOP(self):
            return self.getToken(stlParser.RELOP, 0)

        def NUMBER(self):
            return self.getToken(stlParser.NUMBER, 0)

        def MINUS(self):
            return self.getToken(stlParser.MINUS, 0)

        def getRuleIndex(self):
            return stlParser.RULE_predicate

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterPredicate"):
                listener.enterPredicate(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitPredicate"):
                listener.exitPredicate(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitPredicate"):
                return visitor.visitPredicate(self)
            else:
                return visitor.visitChildren(self)

    def predicate(self):

        localctx = stlParser.PredicateContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_predicate)
        self._la = 0  # Token type
        try:
            self.state = 66
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input, 9, self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 60
                _la = self._input.LA(1)
                if _la == stlParser.MINUS:
                    self.state = 59
                    self.match(stlParser.MINUS)

                self.state = 62
                self.match(stlParser.NAME)
                self.state = 63
                self.match(stlParser.RELOP)
                self.state = 64
                self.match(stlParser.NUMBER)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 65
                self.match(stlParser.NAME)
                pass

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class IntervalContext(ParserRuleContext):
        def __init__(self, parser, parent: ParserRuleContext = None, invokingState: int = -1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def COMMA(self):
            return self.getToken(stlParser.COMMA, 0)

        def LPAREN(self):
            return self.getToken(stlParser.LPAREN, 0)

        def LBRACK(self):
            return self.getToken(stlParser.LBRACK, 0)

        def NUMBER(self, i: int = None):
            if i is None:
                return self.getTokens(stlParser.NUMBER)
            else:
                return self.getToken(stlParser.NUMBER, i)

        def INF(self, i: int = None):
            if i is None:
                return self.getTokens(stlParser.INF)
            else:
                return self.getToken(stlParser.INF, i)

        def RPAREN(self):
            return self.getToken(stlParser.RPAREN, 0)

        def RBRACK(self):
            return self.getToken(stlParser.RBRACK, 0)

        def getRuleIndex(self):
            return stlParser.RULE_interval

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterInterval"):
                listener.enterInterval(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitInterval"):
                listener.exitInterval(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitInterval"):
                return visitor.visitInterval(self)
            else:
                return visitor.visitChildren(self)

    def interval(self):

        localctx = stlParser.IntervalContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_interval)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 68
            _la = self._input.LA(1)
            if not (_la == stlParser.LPAREN or _la == stlParser.LBRACK):
                self._errHandler.recoverInline(self)
            else:
                self.consume()
            self.state = 69
            _la = self._input.LA(1)
            if not (_la == stlParser.INF or _la == stlParser.NUMBER):
                self._errHandler.recoverInline(self)
            else:
                self.consume()
            self.state = 70
            self.match(stlParser.COMMA)
            self.state = 71
            _la = self._input.LA(1)
            if not (_la == stlParser.INF or _la == stlParser.NUMBER):
                self._errHandler.recoverInline(self)
            else:
                self.consume()
            self.state = 72
            _la = self._input.LA(1)
            if not (_la == stlParser.RPAREN or _la == stlParser.RBRACK):
                self._errHandler.recoverInline(self)
            else:
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    def sempred(self, localctx: RuleContext, ruleIndex: int, predIndex: int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[1] = self.phi_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def phi_sempred(self, localctx: PhiContext, predIndex: int):
        if predIndex == 0:
            return self.precpred(self._ctx, 5)

        if predIndex == 1:
            return self.precpred(self._ctx, 4)

        if predIndex == 2:
            return self.precpred(self._ctx, 3)

        if predIndex == 3:
            return self.precpred(self._ctx, 2)
