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
    # Basic / Structural
    IDENTIFIER = auto()
    INTEGER = auto()
    NEWLINE = auto()
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
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
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
