# Parser structured errors

from dataclasses import dataclass
try:
    from lexer.tokens import Token
except ImportError:
    from src.lexer.tokens import Token


@dataclass(frozen=True, slots=True)
class ParseError(Exception):
    message: str
    token: Token

    def __str__(self) -> str:
        lexeme_repr = repr(self.token.lexeme) if self.token.lexeme else self.token.type.name
        return f"ParseError [Line {self.token.line}, Col {self.token.column}]: {self.message} at {lexeme_repr}"
