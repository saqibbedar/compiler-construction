# scanning, recognition, indentation and recovery

from .errors import LexicalError
from .tokens import KEYWORDS, Token, TokenType

# Characters that safely delimit tokens and stop panic mode
SYNCHRONIZERS = set(" \t\r\n()[]{}:,;=+-*/%<>")

"""
Lexer class
"""


class Lexer:
    # constructor
    def __init__(self, source: str) -> None:
        self.source: str = source
        self.position: int = 0
        self.line: int = 1
        self.column: int = 1

        # Error collector
        self.errors: list[LexicalError] = []

    # Main scanner function
    def scan_tokens(self) -> list[Token]:
        # token collector
        tokens: list[Token] = []

        """
        - Main scanner loop
        - self.source string (provided source), loop through it until last character or word
        """
        while self.position < len(self.source):
            # get character from str
            char: str = self.source[self.position]

            # 1. Skip spaces & carriage returns
            if char in " \r":
                self._advance()
                continue

            # 2. Physical newline
            if char == "\n":
                tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))
                self._advance()
                continue

            # 3. Delimiters (single characters)
            if char == "(":
                tokens.append(Token(TokenType.LPAREN, "(", self.line, self.column))
                self._advance()
                continue

            if char == ")":
                tokens.append(Token(TokenType.RPAREN, ")", self.line, self.column))
                self._advance()
                continue

            if char == "[":
                tokens.append(Token(TokenType.LBRACKET, "[", self.line, self.column))
                self._advance()
                continue

            if char == "]":
                tokens.append(Token(TokenType.RBRACKET, "]", self.line, self.column))
                self._advance()
                continue

            if char == "{":
                tokens.append(Token(TokenType.LBRACE, "{", self.line, self.column))
                self._advance()
                continue

            if char == "}":
                tokens.append(Token(TokenType.RBRACE, "}", self.line, self.column))
                self._advance()
                continue

            if char == ",":
                tokens.append(Token(TokenType.COMMA, ",", self.line, self.column))
                self._advance()
                continue

            if char == ":":
                tokens.append(Token(TokenType.COLON, ":", self.line, self.column))
                self._advance()
                continue

            # 4. Dot (.) and Range (..)
            if char == ".":
                col = self.column
                if self._peek(1) == ".":
                    tokens.append(Token(TokenType.RANGE, "..", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.DOT, ".", self.line, col))
                    self._advance()
                continue

            # 5. Operators with multi-char lookahead
            if char == "/":
                col = self.column
                if self._peek(1) == "/":
                    tokens.append(Token(TokenType.FLOOR_DIV, "//", self.line, col))
                    self._advance()
                    self._advance()
                elif self._peek(1) == "=":
                    tokens.append(Token(TokenType.DIV_EQ, "/=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.DIV, "/", self.line, col))
                    self._advance()
                continue

            if char == "*":
                col = self.column
                if self._peek(1) == "*":
                    tokens.append(Token(TokenType.POW, "**", self.line, col))
                    self._advance()
                    self._advance()
                elif self._peek(1) == "=":
                    tokens.append(Token(TokenType.MUL_EQ, "*=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.MUL, "*", self.line, col))
                    self._advance()
                continue

            if char == "+":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.PLUS_EQ, "+=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.PLUS, "+", self.line, col))
                    self._advance()
                continue

            if char == "-":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.MINUS_EQ, "-=", self.line, col))
                    self._advance()
                    self._advance()
                elif self._peek(1) == ">":
                    tokens.append(Token(TokenType.ARROW, "->", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.MINUS, "-", self.line, col))
                    self._advance()
                continue

            if char == "%":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.MOD_EQ, "%=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.MOD, "%", self.line, col))
                    self._advance()
                continue

            if char == "=":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.EQ, "==", self.line, col))
                    self._advance()
                    self._advance()
                elif self._peek(1) == ">":
                    tokens.append(Token(TokenType.FAT_ARROW, "=>", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.ASSIGN, "=", self.line, col))
                    self._advance()
                continue

            if char == "!":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.NOT_EQ, "!=", self.line, col))
                    self._advance()
                    self._advance()
                    continue
                # Isolated '!' is illegal in C--
                tokens.append(self._panic_recovery())
                continue

            if char == "<":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.LT_EQ, "<=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.LT, "<", self.line, col))
                    self._advance()
                continue

            if char == ">":
                col = self.column
                if self._peek(1) == "=":
                    tokens.append(Token(TokenType.GT_EQ, ">=", self.line, col))
                    self._advance()
                    self._advance()
                else:
                    tokens.append(Token(TokenType.GT, ">", self.line, col))
                    self._advance()
                continue

            # 6. Identifier or Keyword
            if char.isascii() and (char.isalpha() or char == "_"):
                tokens.append(self._identifier())
                continue

            # 7. Integer or Malformed Identifier (e.g. 3y)
            if char.isascii() and char.isdigit():
                tokens.append(self._integer_or_malformed())
                continue

            # 8. Panic Mode Fallback
            tokens.append(self._panic_recovery())

        # Terminate a final non-empty statement even without a trailing
        # physical newline.
        # Trailing newline and EOF
        if tokens and tokens[-1].type != TokenType.NEWLINE:
            tokens.append(Token(TokenType.NEWLINE, "", self.line, self.column))

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))

        return tokens

    # =====================================================
    # Internal methods
    # Cursor Movement & Lookahead Methods
    # =====================================================

    def _peek(self, offset: int = 1) -> str:
        """
        Look ahead into the source buffer without consuming characters.
        Parameters:
            offset: The distance from the current position to inspect.
                    offset=1 inspects the immediately following character.
        Returns:
            The character at (self.position + offset), or an empty string ""
            if the offset exceeds the bounds of the source text.
        """
        idx = self.position + offset
        if idx < len(self.source):
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        """
        Consume the current character and advance the 2D cursor coordinates.
        Operation:
            1. Reads the character at self.position.
            2. Advances self.position by 1 index.
            3. Updates self.line and self.column:
               - On newline ('\\n'): increments line counter and resets column to 1.
               - Otherwise: increments column counter by 1.
        Returns:
            The consumed character.
        """
        char: str = self.source[self.position]
        self.position += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _identifier(self) -> Token:
        """
        Scan an identifier or keyword using Maximal Munch.
        Grammar Rule:
            IDENTIFIER = [A-Za-z_][A-Za-z0-9_]*
        Process:
            1. Greedily consumes letters, digits, and underscores.
            2. Compares the resulting lexeme against the KEYWORDS dictionary.
            3. Emits the specific keyword TokenType (e.g. IF, WHILE) if matched,
               or defaults to TokenType.IDENTIFIER.
        Returns:
            A Token instance representing the identifier or keyword.
        """
        start: int = self.position
        line: int = self.line
        column: int = self.column
        while self.position < len(self.source):
            char: str = self.source[self.position]
            if not (char.isascii() and (char.isalnum() or char == "_")):
                break
            self._advance()
        lexeme = self.source[start : self.position]
        # Match against keywords; default to IDENTIFIER
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        return Token(type=token_type, lexeme=lexeme, line=line, column=column)

    def _integer_or_malformed(self) -> Token:
        """
        Scan an integer literal and detect invalid identifiers starting with digits.
        Grammar Rules:
            INTEGER = [0-9]+
            INVALID_ID = [0-9]+[A-Za-z_][A-Za-z0-9_]* (e.g. 3y, 10var)
        Process:
            1. Consumes all consecutive digits.
            2. Lookahead check: if immediately followed by an ASCII letter or '_',
               this violates language naming rules (variables cannot start with digits).
            3. On violation: enters panic mode, hoards the rest of the token until
               a SYNCHRONIZER is reached, appends a LexicalError, and returns Token(ERROR).
            4. Otherwise: returns a valid Token(INTEGER).
        Returns:
            A Token instance of TokenType.INTEGER or TokenType.ERROR.
        """
        start: int = self.position
        line: int = self.line
        column: int = self.column
        while (
            self.position < len(self.source)
            and self.source[self.position].isascii()
            and self.source[self.position].isdigit()
        ):
            self._advance()
        # Malformed check: digits followed by letter/_ (e.g. 3y)
        if (
            self.position < len(self.source)
            and self.source[self.position].isascii()
            and (self.source[self.position].isalpha() or self.source[self.position] == "_")
        ):
            while self.position < len(self.source) and self.source[self.position] not in SYNCHRONIZERS:
                self._advance()
            lexeme = self.source[start : self.position]
            err = LexicalError(
                message=f"Invalid identifier starting with digit: {lexeme!r}",
                lexeme=lexeme,
                line=line,
                column=column,
            )
            self.errors.append(err)
            return Token(TokenType.ERROR, lexeme, line, column)
        return Token(TokenType.INTEGER, self.source[start : self.position], line, column)

    def _panic_recovery(self) -> Token:
        """
        Recover from unknown characters by hoarding until the next synchronizer.
        Usage:
            Called as the fallback in scan_tokens when a character is not recognized
            by any valid rule (e.g. '$' in '9$n53bqa)$49').
        Process:
            1. Captures start coordinates.
            2. Consumes consecutive illegal/unclassified characters until hitting
               any character in SYNCHRONIZERS or EOF.
            3. Records a structured LexicalError in self.errors.
            4. Emits a Token(TokenType.ERROR) so the parser/caller can inspect it.
        Returns:
            A Token instance of TokenType.ERROR.
        """
        start: int = self.position
        line: int = self.line
        column: int = self.column
        while self.position < len(self.source) and self.source[self.position] not in SYNCHRONIZERS:
            self._advance()
        lexeme = self.source[start : self.position]
        err = LexicalError(
            message=f"Unexpected token in panic mode: {lexeme!r}",
            lexeme=lexeme,
            line=line,
            column=column,
        )
        self.errors.append(err)
        return Token(TokenType.ERROR, lexeme, line, column)
