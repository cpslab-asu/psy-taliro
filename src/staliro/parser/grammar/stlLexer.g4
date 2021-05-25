lexer grammar stlLexer;

options {
    language = Python3;
}

WS
    : [ \t\r\n]+ -> skip ;

LPAREN
    : '(' ;

RPAREN
    : ')' ;

LBRACK
    : '[' ;

RBRACK
    : ']' ;

COMMA
    : ',' ;

MINUS
    : '-' ;

NEGATION
    : ('~' | '!' | 'not') ;

RELOP
    : ('<' | '>' | '<=' | '>=') ;

EQUALITYOP
    : ('==' | '!=') ;

NEXTOP
    : ('next' | 'X') ('_')? ;

FUTUREOP
    : ('finally' | 'eventually' | 'F' | '<>') ;

GLOBALLYOP
    : ('globally' | 'always' | 'G' | '[]') ;

UNTILOP
    : ('until' | 'U') ;

RELEASEOP
    : ('release' | 'R') ;

ANDOP
    : ('and' | '/\\' | '&&' | '&') ;

OROP
    : ('or' | '\\/' | '||' | '|') ;

IMPLIESOP
    : ('implies' | '->') ;

EQUIVOP
    : ('iff' | '<->') ;

INF
    : 'inf' ;

NAME
    : LETTER (LETTER | [0-9] | '_')* ;

NUMBER
    : (MINUS)? INT_NUMBER
    | (MINUS)? FLOAT_NUMBER
;

INT_NUMBER
    : DECIMAL_INTEGER ;

FLOAT_NUMBER
    : POINT_FLOAT ;

fragment DECIMAL_INTEGER
    : NON_ZERO_DIGIT DIGIT*
    | '0'+
;

fragment NON_ZERO_DIGIT
    : [1-9] ;

fragment DIGIT
    : [0-9] ;

fragment POINT_FLOAT
    : DIGIT? FRACTION
    | DIGIT '.'
;

fragment FRACTION
    : '.' DIGIT+
;

fragment Digits
    : [0-9]+ ;

fragment PREFIX
    : 'Var_' ;

fragment LETTER
    : [a-zA-Z]+ ;
