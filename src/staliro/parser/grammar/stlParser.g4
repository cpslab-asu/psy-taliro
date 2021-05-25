parser grammar stlParser;

options {
    language = Python3;
    tokenVocab = stlLexer;
}

stlSpecification
    : phi EOF ;

phi
    : LPAREN phi RPAREN              #parenPhiExpr

    | NEGATION phi                   #opNegExpr

    | NEXTOP        (interval)? phi  #opNextExpr
    | FUTUREOP      (interval)? phi  #opFutureExpr
    | GLOBALLYOP    (interval)? phi  #opGloballyExpr

    | phi UNTILOP   (interval)? phi  #opUntilExpr
    | phi RELEASEOP (interval)? phi  #opReleaseExpr

    | phi (ANDOP | OROP) phi         #opLogicalExpr

    | phi (IMPLIESOP | EQUIVOP) phi  #opPropExpr

    | predicate                      #predicateExpr
;

predicate
    : (MINUS)? NAME RELOP NUMBER
    | NAME
;

interval
    : (LPAREN | LBRACK) (NUMBER | INF) COMMA (NUMBER | INF) (RPAREN | RBRACK)
;
