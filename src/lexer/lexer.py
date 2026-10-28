# scanning, recognition, indentation and recovery

from .errors import LexicalError
from .tokens import KEYWORDS, Token, TokenType

# Characters that safely delimit tokens and stop panic mode
SYNCHRONIZERS = set(" \t\r\n()[]{}:;,=+-*/%<>.")

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
            if char in " \t\r":
                self._advance()
                continue

            # 1b. singleline comment (#...)
            if char == "#":
                # Consume until physical newline or end of file

                while self.position < len(self.source) and self.source[self.position] != "\n":
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

                # Multi-line block comment: /* ... */
                if self._peek(1) == "*":
                    start_line = self.line
                    self._advance()  # consume '/'
                    self._advance()  # consume '*'
                    while self.position < len(self.source):
                        if self.source[self.position] == "*" and self._peek(1) == "/":
                            self._advance()  # consume '*'
                            self._advance()  # consume '/'
                            break
                        self._advance()
                    else:
                        # Reached EOF without closing '*/'
                        err = LexicalError(
                            message="Unterminated block comment",
                            lexeme="/*",
                            line=start_line,
                            column=col,
                        )
                        self.errors.append(err)
                        tokens.append(Token(TokenType.ERROR, "/*", start_line, col))
                    continue

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
        start: int = self.position
        line: int = self.line
        column: int = self.column

        # 1. Consume valid identifier characters: [A-Za-z_][A-Za-z0-9_]*
        while self.position < len(self.source):
            char: str = self.source[self.position]
            if not (char.isascii() and (char.isalnum() or char == "_")):
                break
            self._advance()

        # 2. Check for illegal characters glued to the identifier (e.g. _for$while, y$fn)
        if self.position < len(self.source) and self.source[self.position] not in SYNCHRONIZERS:
            # Hoard the illegal character(s) and rest of the token until a synchronizer
            while self.position < len(self.source) and self.source[self.position] not in SYNCHRONIZERS:
                self._advance()

            lexeme = self.source[start : self.position]
            err = LexicalError(
                message=f"Invalid identifier containing illegal character: {lexeme!r}",
                lexeme=lexeme,
                line=line,
                column=column,
            )
            self.errors.append(err)
            return Token(TokenType.ERROR, lexeme, line, column)

        # 3. Match against keywords; default to IDENTIFIER
        lexeme = self.source[start : self.position]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        return Token(type=token_type, lexeme=lexeme, line=line, column=column)

    def _integer_or_malformed(self) -> Token:
        start: int = self.position
        line: int = self.line
        column: int = self.column

        # 1. Consume integer part
        while (
            self.position < len(self.source)
            and self.source[self.position].isascii()
            and self.source[self.position].isdigit()
        ):
            self._advance()

        is_float = False

        # 2. Check for fractional part: '.' followed by digit
        # (Preserves '..' range operator so 1..10 is not broken)
        if (
            self.position < len(self.source)
            and self.source[self.position] == "."
            and self._peek(1).isdigit()
        ):
            is_float = True
            self._advance()  # consume '.'
            while (
                self.position < len(self.source)
                and self.source[self.position].isascii()
                and self.source[self.position].isdigit()
            ):
                self._advance()

        # 3. Detect malformed float with multiple dots: e.g. 7.34.4
        if (
            self.position < len(self.source)
            and self.source[self.position] == "."
            and self._peek(1) != "."  # not the start of a '..' range
        ):
            while self.position < len(self.source) and self.source[self.position] not in SYNCHRONIZERS:
                self._advance()
            lexeme = self.source[start : self.position]
            err = LexicalError(
                message=f"Malformed float literal with multiple decimal points: {lexeme!r}",
                lexeme=lexeme,
                line=line,
                column=column,
            )
            self.errors.append(err)
            return Token(TokenType.ERROR, lexeme, line, column)

        # 4. Detect invalid identifier starting with digit: e.g. 3y, 7.34var
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

        lexeme = self.source[start : self.position]
        token_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(token_type, lexeme, line, column)

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

        # 1. Always advance at least once to guarantee forward progress
        self._advance()

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
