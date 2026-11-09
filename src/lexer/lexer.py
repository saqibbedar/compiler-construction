# scanning, recognition, indentation and recovery

from .errors import LexicalError
from .tokens import KEYWORDS, Token, TokenType

# Characters that safely delimit tokens and stop panic mode
# ('!' '#' ';' and the quote characters start a new token, so they must end an identifier or number)
SYNCHRONIZERS = set(" \t\r\n()[]{}:,=+-*/%<>.!#;\"'`")

"""
Lexer class
"""


class Lexer:
    # constructor
    def __init__(self, source: str) -> None:
        # Drop a UTF-8 byte order mark (added by some Windows editors) so it is not lexed as a token
        self.source: str = source.removeprefix("﻿")
        self.position: int = 0
        self.line: int = 1
        self.column: int = 1

        # Error collector
        self.errors: list[LexicalError] = []

        # Stack tracking brace depth inside backtick interpolation expressions
        self.interpolation_brace_depths: list[int] = []

        # Indentation stack tracking indentation levels (measured in spaces)
        self.indent_stack: list[int] = [0]

        # Nesting depth for grouping delimiters: (), [], and {} (outside backtick text)
        self.delimiter_depth: int = 0

        # State tracking whether the scanner is at the start of a logical line
        self.at_line_start: bool = True

    # Main scanner function
    def scan_tokens(self) -> list[Token]:
        # token collector
        tokens: list[Token] = []

        """
        - Main scanner loop
        - self.source string (provided source), loop through it until last character or word
        """
        while self.position < len(self.source):
            # 0. Handle line-start indentation when outside grouping delimiters
            if self.at_line_start and self.delimiter_depth == 0:
                self._handle_line_start(tokens)
                if self.position >= len(self.source):
                    break

            # get character from str
            char: str = self.source[self.position]

            # 1. Skip spaces & carriage returns within a line
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
                line = self.line
                col = self.column
                self._advance()

                if self.delimiter_depth > 0:
                    # Inside (), [], {} grouping delimiters: newlines are ignored (implicit continuation)
                    continue

                # Logical NEWLINE terminates statement:
                # Only emit if previous token was not already a NEWLINE or INDENT
                if tokens and tokens[-1].type not in (TokenType.NEWLINE, TokenType.INDENT):
                    tokens.append(Token(TokenType.NEWLINE, "\n", line, col))

                self.at_line_start = True
                continue

            # 3. Delimiters (single characters)
            if char == "(":
                self.delimiter_depth += 1
                tokens.append(Token(TokenType.LPAREN, "(", self.line, self.column))
                self._advance()
                continue

            if char == ")":
                if self.delimiter_depth > 0:
                    self.delimiter_depth -= 1
                tokens.append(Token(TokenType.RPAREN, ")", self.line, self.column))
                self._advance()
                continue

            if char == "[":
                self.delimiter_depth += 1
                tokens.append(Token(TokenType.LBRACKET, "[", self.line, self.column))
                self._advance()
                continue

            if char == "]":
                if self.delimiter_depth > 0:
                    self.delimiter_depth -= 1
                tokens.append(Token(TokenType.RBRACKET, "]", self.line, self.column))
                self._advance()
                continue

            if char == "{":
                self.delimiter_depth += 1
                if self.interpolation_brace_depths:
                    self.interpolation_brace_depths[-1] += 1
                tokens.append(Token(TokenType.LBRACE, "{", self.line, self.column))
                self._advance()
                continue

            if char == "}":
                if self.delimiter_depth > 0:
                    self.delimiter_depth -= 1
                if self.interpolation_brace_depths:
                    self.interpolation_brace_depths[-1] -= 1
                    tokens.append(Token(TokenType.RBRACE, "}", self.line, self.column))
                    self._advance()

                    if self.interpolation_brace_depths[-1] == 0:
                        self.interpolation_brace_depths.pop()
                        # Exit expression mode; resume scanning subsequent backtick string chunk
                        self._scan_backtick_chunk(tokens, is_opening=False)
                    continue

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

            # Double and Single quoted strings (no interpolation)
            if char in ('"', "'"):
                tokens.append(self._string(quote=char))
                continue

            # Backtick strings (support interpolation)
            if char == "`":
                self._scan_backtick_chunk(tokens, is_opening=True)
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

        # Check if an interpolation was left unclosed at EOF
        if self.interpolation_brace_depths:
            err = LexicalError(
                message="Unterminated string interpolation: missing '}'",
                lexeme="",
                line=self.line,
                column=self.column,
            )
            self.errors.append(err)
            tokens.append(Token(TokenType.ERROR, "", self.line, self.column))

        # Check if a grouping delimiter was left unclosed at EOF
        # (an unclosed interpolation brace is already reported above, so skip the duplicate)
        if self.delimiter_depth > 0 and not self.interpolation_brace_depths:
            err = LexicalError(
                message="Unclosed grouping delimiter at end of file",
                lexeme="",
                line=self.line,
                column=self.column,
            )
            self.errors.append(err)
            tokens.append(Token(TokenType.ERROR, "", self.line, self.column))

        # Terminate a final statement with NEWLINE if needed
        if tokens and tokens[-1].type not in (TokenType.NEWLINE, TokenType.DEDENT):
            tokens.append(Token(TokenType.NEWLINE, "", self.line, self.column))

        # Drain any remaining indentation levels from indent_stack
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, "", self.line, self.column))

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))

        return tokens

    # =====================================================
    # Internal methods: Indentation & Line Handling
    # =====================================================

    def _peek_line_indentation(self) -> tuple[int, bool, int | None]:
        """
        Inspect the leading whitespace from self.position up to the first non-whitespace character.
        Returns:
            (indent_count, has_tab, first_non_whitespace_index)
            If the line is blank (only whitespace followed by \\n or EOF), first_non_whitespace_index is None.
        """
        idx = self.position
        indent_count = 0
        has_tab = False

        while idx < len(self.source):
            c = self.source[idx]
            if c == " ":
                indent_count += 1
                idx += 1
            elif c == "\t":
                has_tab = True
                indent_count += 4
                idx += 1
            elif c == "\r":
                idx += 1
            elif c == "\n":
                return indent_count, has_tab, None
            else:
                return indent_count, has_tab, idx

        return indent_count, has_tab, None

    def _is_block_comment_alone_on_line(self, start_idx: int) -> bool:
        """
        Check if the block comment starting at start_idx has no code after it on the same line.
        """
        # A line made only of block comments (optionally followed by a '#' comment) carries no code,
        # so it must not take part in indentation handling
        idx = start_idx
        while True:
            end_idx = self.source.find("*/", idx + 2)
            if end_idx == -1:
                return False
            idx = end_idx + 2
            while idx < len(self.source) and self.source[idx] in " \t\r":
                idx += 1
            if self.source.startswith("/*", idx):
                continue
            return idx >= len(self.source) or self.source[idx] in "\n#"

    def _consume_blank_line(self) -> None:
        while self.position < len(self.source) and self.source[self.position] != "\n":
            self._advance()
        if self.position < len(self.source) and self.source[self.position] == "\n":
            self._advance()

    def _consume_comment_line(self) -> None:
        while self.position < len(self.source) and self.source[self.position] != "\n":
            self._advance()
        if self.position < len(self.source) and self.source[self.position] == "\n":
            self._advance()

    def _consume_block_comment_line(self) -> None:
        # Advance through whitespace before /*
        while self.position < len(self.source) and self.source[self.position] in " \t\r":
            self._advance()
        # Advance through /*
        self._advance()
        self._advance()
        while self.position < len(self.source):
            if self.source[self.position] == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                break
            self._advance()
        # Advance through whitespace after */ up to newline
        while self.position < len(self.source) and self.source[self.position] in " \t\r":
            self._advance()
        if self.position < len(self.source) and self.source[self.position] == "\n":
            self._advance()

    def _handle_line_start(self, tokens: list[Token]) -> None:
        while self.position < len(self.source) and self.at_line_start and self.delimiter_depth == 0:
            indent_count, has_tab, first_char_idx = self._peek_line_indentation()

            # Blank line (only whitespace up to newline or EOF)
            if first_char_idx is None:
                self._consume_blank_line()
                continue

            first_char = self.source[first_char_idx]

            # Single-line comment (#...)
            if first_char == "#":
                self._consume_comment_line()
                continue

            # Block comment (/*...*/) alone on line
            if (
                first_char == "/"
                and first_char_idx + 1 < len(self.source)
                and self.source[first_char_idx + 1] == "*"
                and self._is_block_comment_alone_on_line(first_char_idx)
            ):
                self._consume_block_comment_line()
                continue

            # Non-blank line containing code: process indentation
            self._process_indentation(tokens, indent_count, has_tab)
            self.at_line_start = False
            break

    def _process_indentation(self, tokens: list[Token], current_indent: int, has_tab: bool) -> None:
        indent_line = self.line
        indent_col = 1

        # 1. Check for tab in indentation
        if has_tab:
            err = LexicalError(
                message="IndentationError: tab character found in indentation; C-- requires 4 spaces",
                lexeme="\t",
                line=indent_line,
                column=indent_col,
            )
            self.errors.append(err)
            tokens.append(Token(TokenType.ERROR, "\t", indent_line, indent_col))

        # 2. Check for multiple of 4
        if current_indent % 4 != 0:
            err = LexicalError(
                message=f"IndentationError: indentation must be a multiple of 4 spaces (got {current_indent} spaces)",
                lexeme=" " * current_indent,
                line=indent_line,
                column=indent_col,
            )
            self.errors.append(err)
            tokens.append(Token(TokenType.ERROR, " " * current_indent, indent_line, indent_col))

        # Advance past the leading whitespace so self.position and self.column point to the first token
        while self.position < len(self.source) and self.source[self.position] in " \t\r":
            self._advance()

        last_indent = self.indent_stack[-1]

        if current_indent > last_indent:
            # 3. Check for indentation before the first statement, or a multi-level jump (e.g. 0 -> 8)
            if not tokens:
                err = LexicalError(
                    message="IndentationError: unexpected indent before the first statement",
                    lexeme=" " * current_indent,
                    line=indent_line,
                    column=indent_col,
                )
                self.errors.append(err)
                tokens.append(Token(TokenType.ERROR, " " * current_indent, indent_line, indent_col))
            elif current_indent > last_indent + 4:
                err = LexicalError(
                    message=f"IndentationError: unexpected indent jump from {last_indent} to {current_indent} spaces",
                    lexeme=" " * current_indent,
                    line=indent_line,
                    column=indent_col,
                )
                self.errors.append(err)
                tokens.append(Token(TokenType.ERROR, " " * current_indent, indent_line, indent_col))

            self.indent_stack.append(current_indent)
            tokens.append(Token(TokenType.INDENT, " " * current_indent, indent_line, indent_col))

        elif current_indent < last_indent:
            # 4. Dedent: pop until stack top <= current_indent
            while self.indent_stack and self.indent_stack[-1] > current_indent:
                self.indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, "", indent_line, indent_col))

            # 5. Check if unindent matches an existing outer level
            if not self.indent_stack or self.indent_stack[-1] != current_indent:
                err = LexicalError(
                    message=f"IndentationError: unindent does not match any outer indentation level ({current_indent} spaces)",
                    lexeme=" " * current_indent,
                    line=indent_line,
                    column=indent_col,
                )
                self.errors.append(err)
                tokens.append(Token(TokenType.ERROR, " " * current_indent, indent_line, indent_col))
                # Treat the odd level as a new one so INDENT/DEDENT stay balanced
                self.indent_stack.append(current_indent)
                tokens.append(Token(TokenType.INDENT, " " * current_indent, indent_line, indent_col))

    # =====================================================
    # Internal methods
    # Cursor Movement & Lookahead Methods
    # =====================================================

    def _string(self, quote: str) -> Token:
        start: int = self.position
        line: int = self.line
        column: int = self.column

        self._advance()  # consume opening quote (' or ")

        while self.position < len(self.source):
            char = self.source[self.position]

            # 1. Escape sequences (\", \', \\, etc.)
            if char == "\\":
                self._advance()  # consume '\'
                if self.position < len(self.source):
                    self._advance()  # consume escaped char
                continue

            # 2. Matching closing quote
            if char == quote:
                self._advance()  # consume closing quote
                lexeme = self.source[start : self.position]
                return Token(TokenType.STRING, lexeme, line, column)

            # 3. Quoted strings are single-line: stop at the newline so one missing quote
            # does not swallow the rest of the file (backtick strings may span lines)
            if char == "\n":
                break

            self._advance()

        # Unterminated string reached end of line or EOF
        lexeme = self.source[start : self.position]
        err = LexicalError(
            message=f"Unterminated string literal: {lexeme!r}",
            lexeme=lexeme,
            line=line,
            column=column,
        )
        self.errors.append(err)
        return Token(TokenType.ERROR, lexeme, line, column)

    def _scan_backtick_chunk(self, tokens: list[Token], is_opening: bool) -> None:
        start: int = self.position
        line: int = self.line
        column: int = self.column

        if is_opening:
            self._advance()  # consume opening '`'

        while self.position < len(self.source):
            char = self.source[self.position]

            # 1. Escape sequences (\`, \{, \\, etc.)
            if char == "\\":
                self._advance()  # consume '\'
                if self.position < len(self.source):
                    self._advance()  # consume escaped char
                continue

            # 2. Closing backtick
            if char == "`":
                self._advance()  # consume closing '`'
                lexeme = self.source[start : self.position]
                tokens.append(Token(TokenType.STRING, lexeme, line, column))
                return

            # 3. Interpolation start: {expr}
            if char == "{":
                lexeme = self.source[start : self.position]
                if lexeme:
                    tokens.append(Token(TokenType.STRING, lexeme, line, column))

                brace_line = self.line
                brace_col = self.column
                tokens.append(Token(TokenType.LBRACE, "{", brace_line, brace_col))
                self._advance()  # consume '{'

                self.delimiter_depth += 1
                self.interpolation_brace_depths.append(1)
                return

            self._advance()

        # Unterminated backtick reached EOF
        lexeme = self.source[start : self.position]
        err = LexicalError(
            message=f"Unterminated backtick string literal: {lexeme!r}",
            lexeme=lexeme,
            line=line,
            column=column,
        )
        self.errors.append(err)
        tokens.append(Token(TokenType.ERROR, lexeme, line, column))

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
        if self.position < len(self.source) and self.source[self.position] == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()  # consume '.'
            while (
                self.position < len(self.source)
                and self.source[self.position].isascii()
                and self.source[self.position].isdigit()
            ):
                self._advance()

        # 3. Detect malformed float: extra decimal point (7.34.4) or no digits after the point (5.)
        if (
            self.position < len(self.source)
            and self.source[self.position] == "."
            and self._peek(1) != "."  # not the start of a '..' range
        ):
            # '.' is a synchronizer, so consume it explicitly (except when it begins a '..' range)
            # or the rest of the bad literal would leak out as separate tokens
            while self.position < len(self.source) and (
                self.source[self.position] not in SYNCHRONIZERS
                or (self.source[self.position] == "." and self._peek(1) != ".")
            ):
                self._advance()
            lexeme = self.source[start : self.position]
            err = LexicalError(
                message=f"Malformed float literal: {lexeme!r}",
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
