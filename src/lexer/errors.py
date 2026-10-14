# structured lexical errors
from dataclasses import dataclass

"""
LexicalError: Error Token
"""


@dataclass(frozen=True, slots=True)
class LexicalError:
    message: str
    lexeme: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"LexicalError [Line {self.line}, Col {self.column}]: {self.message} -> {self.lexeme!r}"
