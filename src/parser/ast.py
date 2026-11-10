# AST node definitions for the C-- language

from dataclasses import dataclass, field
try:
    from lexer.tokens import Token, TokenType
except ImportError:
    from src.lexer.tokens import Token, TokenType


@dataclass(slots=True)
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


# =====================================================
# Types
# =====================================================

@dataclass(slots=True)
class TypeNode(ASTNode):
    name: str = ""
    type_args: list["TypeNode"] = field(default_factory=list)

    def __repr__(self) -> str:
        if self.type_args:
            args_str = ", ".join(repr(arg) for arg in self.type_args)
            return f"{self.name}[{args_str}]"
        return self.name


# =====================================================
# Expressions
# =====================================================

@dataclass(slots=True)
class Expression(ASTNode):
    """Base class for expression nodes."""
    pass


@dataclass(slots=True)
class LiteralExpr(Expression):
    value: int | float | str | bool | None = None
    raw: str = ""


@dataclass(slots=True)
class IdentifierExpr(Expression):
    name: str = ""


@dataclass(slots=True)
class BinaryExpr(Expression):
    left: Expression = field(default_factory=Expression)
    op: Token = field(default_factory=lambda: Token(TokenType.ERROR, "", 0, 0))
    right: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class UnaryExpr(Expression):
    op: Token = field(default_factory=lambda: Token(TokenType.ERROR, "", 0, 0))
    operand: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class ConditionalExpr(Expression):
    condition: Expression = field(default_factory=Expression)
    true_expr: Expression = field(default_factory=Expression)
    false_expr: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class CallExpr(Expression):
    callee: Expression = field(default_factory=Expression)
    arguments: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class IndexExpr(Expression):
    target: Expression = field(default_factory=Expression)
    index: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class SliceExpr(Expression):
    start: Expression | None = None
    stop: Expression | None = None
    step: Expression | None = None


@dataclass(slots=True)
class MemberAccessExpr(Expression):
    target: Expression = field(default_factory=Expression)
    member: str = ""


@dataclass(slots=True)
class ListExpr(Expression):
    elements: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class TupleExpr(Expression):
    elements: list[Expression] = field(default_factory=list)


@dataclass(slots=True)
class DictExpr(Expression):
    pairs: list[tuple[Expression, Expression]] = field(default_factory=list)


@dataclass(slots=True)
class StringInterpolationExpr(Expression):
    parts: list[Expression | str] = field(default_factory=list)


@dataclass(slots=True)
class Parameter(ASTNode):
    name: str = ""
    type_annotation: TypeNode | None = None


@dataclass(slots=True)
class ArrowFunctionExpr(Expression):
    params: list[Parameter] = field(default_factory=list)
    return_type: TypeNode | None = None
    body: Expression = field(default_factory=Expression)


# =====================================================
# Statements
# =====================================================

@dataclass(slots=True)
class Statement(ASTNode):
    """Base class for statement nodes."""
    pass


@dataclass(slots=True)
class ExpressionStmt(Statement):
    expression: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class VariableDeclStmt(Statement):
    name: str = ""
    type_annotation: TypeNode | None = None
    value: Expression | None = None


@dataclass(slots=True)
class AssignmentStmt(Statement):
    target: Expression = field(default_factory=Expression)
    value: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class AugmentedAssignStmt(Statement):
    target: Expression = field(default_factory=Expression)
    op: Token = field(default_factory=lambda: Token(TokenType.ERROR, "", 0, 0))
    value: Expression = field(default_factory=Expression)


@dataclass(slots=True)
class FunctionDefStmt(Statement):
    name: str = ""
    params: list[Parameter] = field(default_factory=list)
    return_type: TypeNode | None = None
    body: list[Statement] = field(default_factory=list)
    is_public: bool = False


@dataclass(slots=True)
class IfStmt(Statement):
    condition: Expression = field(default_factory=Expression)
    then_branch: list[Statement] = field(default_factory=list)
    elif_branches: list[tuple[Expression, list[Statement]]] = field(default_factory=list)
    else_branch: list[Statement] | None = None


@dataclass(slots=True)
class WhileStmt(Statement):
    condition: Expression = field(default_factory=Expression)
    body: list[Statement] = field(default_factory=list)


@dataclass(slots=True)
class ForStmt(Statement):
    target: str = ""
    iterable: Expression = field(default_factory=Expression)
    body: list[Statement] = field(default_factory=list)


@dataclass(slots=True)
class CaseClause(ASTNode):
    pattern: Expression = field(default_factory=Expression)
    guard: Expression | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass(slots=True)
class MatchStmt(Statement):
    subject: Expression = field(default_factory=Expression)
    cases: list[CaseClause] = field(default_factory=list)


@dataclass(slots=True)
class ReturnStmt(Statement):
    value: Expression | None = None


@dataclass(slots=True)
class BreakStmt(Statement):
    pass


@dataclass(slots=True)
class ContinueStmt(Statement):
    pass


@dataclass(slots=True)
class ImportStmt(Statement):
    module: str = ""
    alias: str | None = None
    symbols: list[tuple[str, str | None]] = field(default_factory=list)


@dataclass(slots=True)
class ClassMember(ASTNode):
    visibility: str = "+"  # '+' for public, '-' for private
    definition: Statement = field(default_factory=Statement)


@dataclass(slots=True)
class FieldDecl(Statement):
    name: str = ""
    type_annotation: TypeNode = field(default_factory=TypeNode)
    init_value: Expression | None = None


@dataclass(slots=True)
class ClassDefStmt(Statement):
    name: str = ""
    heritage: list[TypeNode] = field(default_factory=list)
    members: list[ClassMember] = field(default_factory=list)
    is_public: bool = False


@dataclass(slots=True)
class SpecDefStmt(Statement):
    name: str = ""
    members: list[Statement] = field(default_factory=list)


# =====================================================
# Root Program
# =====================================================

@dataclass(slots=True)
class Program(ASTNode):
    statements: list[Statement] = field(default_factory=list)


# =====================================================
# AST Formatter / Visual Dumper
# =====================================================

def dump_ast(node: object, indent: int = 0) -> str:
    """Format an AST node or subtree into a clean, human-readable indented string."""
    pad = "  " * indent
    if node is None:
        return f"{pad}None"
    if isinstance(node, list):
        if not node:
            return f"{pad}[]"
        lines = [f"{pad}["]
        for item in node:
            lines.append(dump_ast(item, indent + 1))
        lines.append(f"{pad}]")
        return "\n".join(lines)
    if isinstance(node, tuple):
        lines = [f"{pad}("]
        for item in node:
            lines.append(dump_ast(item, indent + 1))
        lines.append(f"{pad})")
        return "\n".join(lines)
    if isinstance(node, ASTNode):
        cls_name = node.__class__.__name__
        field_lines: list[str] = []
        for attr in getattr(node, "__slots__", []):
            if attr in ("line", "column"):
                continue
            val = getattr(node, attr, None)
            if isinstance(val, (ASTNode, list, tuple)):
                dumped = dump_ast(val, indent + 1).strip()
                field_lines.append(f"{pad}  {attr}=\n{pad}    {dumped}")
            else:
                field_lines.append(f"{pad}  {attr}={val!r}")
        if not field_lines:
            return f"{pad}{cls_name}()"
        inner = "\n".join(field_lines)
        return f"{pad}{cls_name}(\n{inner}\n{pad})"
    return f"{pad}{node!r}"
