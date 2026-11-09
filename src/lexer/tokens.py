# token types and token representation

from dataclasses import dataclass
from enum import IntEnum, auto

# Token dictionary is readable and also faster but not safe and also for bad for type hinting and code safety
# TokDict = {
#     "IDENTIFIER": None,
#     "ASSIGN": None
# }

"""
TokenTypes Dictionary: utilizing enums for maximum safety.

Inheriting from IntEnum, its better in performance and balanced approach between dictionary, as attributes gets auto increment integer assignment starting from 1...n. And, it is significantly faster than standard Enum because it has built-in int type.
"""


class TokenType(IntEnum):
    # Basic / Structural & Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()
    ERROR = auto()

    # 1. Keywords
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    FOR = auto()
    IN = auto()
    WHILE = auto()
    MATCH = auto()
    CASE = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    PUB = auto()
    FN = auto()
    CLASS = auto()
    SPEC = auto()
    NONE = auto()
    TRUE = auto()
    FALSE = auto()
    INPUT = auto()
    PRINT = auto()

    # 2. Arithmetic operators
    PLUS = auto()  # +
    MINUS = auto()  # -
    MUL = auto()  # *
    DIV = auto()  # /
    MOD = auto()  # %
    POW = auto()  # **
    FLOOR_DIV = auto()  # //

    # 3. Comparison operators
    EQ = auto()  # ==
    NOT_EQ = auto()  # !=
    GT = auto()  # >
    LT = auto()  # <
    GT_EQ = auto()  # >=
    LT_EQ = auto()  # <=

    # 4. Logical operators
    AND = auto()  # and
    OR = auto()  # or
    NOT = auto()  # not

    # 5. Assignment operators
    ASSIGN = auto()  # =
    PLUS_EQ = auto()  # +=
    MINUS_EQ = auto()  # -=
    MUL_EQ = auto()  # *=
    DIV_EQ = auto()  # /=
    MOD_EQ = auto()  # %=

    # 6. Range & Delimiters
    RANGE = auto()  # ..
    DOT = auto()  # .
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    COMMA = auto()  # ,
    COLON = auto()  # :

    # 7. Arrows (two different tokens, never interchangeable)
    #
    # ARROW  (->)  "thin arrow": introduces the return type of a named function.
    #                  fn add(a: int, b: int) -> int:
    #              Lexeme is always the two characters '->'.
    #
    # FAT_ARROW (=>)  "fat arrow": separates what comes before from what it produces. Used in two places:
    #   1. arrow functions (anonymous functions), which start with the 'fn' keyword. '=>' separates the
    #      parameter list (and optional ': type' return annotation) from the one-expression body:
    #          add = fn(a: int, b: int): int => a + b
    #          double = fn(x) => x * 2
    #          now = fn() => 42
    #   2. match arms, where it separates the pattern from the arm's block:
    #          case 1, 2 => print("low")
    #   Lexeme is always the two characters '=>'. It is a single token, so 'fn(x)=>x' and 'fn(x) => x'
    #   scan identically, and it is never confused with '>=' (GT_EQ) or '==' (EQ).
    #   A lone '=' (ASSIGN) or '>' (GT) next to each other with whitespace between ('= >') are two tokens.
    ARROW = auto()  # ->
    FAT_ARROW = auto()  # =>


# Keyword lookup dictionary
KEYWORDS: dict[str, TokenType] = {
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "while": TokenType.WHILE,
    "match": TokenType.MATCH,
    "case": TokenType.CASE,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "return": TokenType.RETURN,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "as": TokenType.AS,
    "pub": TokenType.PUB,
    "fn": TokenType.FN,
    "class": TokenType.CLASS,
    "spec": TokenType.SPEC,
    "None": TokenType.NONE,
    "none": TokenType.NONE,
    "true": TokenType.BOOL,
    "false": TokenType.BOOL,
    "True": TokenType.BOOL,
    "False": TokenType.BOOL,
    "input": TokenType.INPUT,
    "print": TokenType.PRINT,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


"""
Token metadata class

# dataclass parameters
- frozen=True makes tokens immutable after creation
- slots=True reduces per-instance overhead and prevents accidental attributes

Explanation: Normal class storage per instance: __dict__, with slots true its fixed size array and saves up to ~60% RAM
"""


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int


# Testing
# print(Token(TokenType.EOF, "\n", 1, 1))             # Token(type=<TokenType.EOF: 5>, lexeme='\n', line=1, column=1)
# print(Token(TokenType.EOF.value, "\n", 1, 1))       # Token(type=5, lexeme='\n', line=1, column=1)
