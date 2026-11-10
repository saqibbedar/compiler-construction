# Recursive-Descent Parser for the C-- language

try:
    from lexer.tokens import Token, TokenType
except ImportError:
    from src.lexer.tokens import Token, TokenType
from .ast import (
    ArrowFunctionExpr,
    AssignmentStmt,
    AugmentedAssignStmt,
    BinaryExpr,
    BreakStmt,
    CallExpr,
    CaseClause,
    ClassDefStmt,
    ClassMember,
    ConditionalExpr,
    ContinueStmt,
    DictExpr,
    Expression,
    ExpressionStmt,
    FieldDecl,
    ForStmt,
    FunctionDefStmt,
    IdentifierExpr,
    IfStmt,
    ImportStmt,
    IndexExpr,
    ListExpr,
    LiteralExpr,
    MatchStmt,
    MemberAccessExpr,
    Parameter,
    Program,
    ReturnStmt,
    SliceExpr,
    SpecDefStmt,
    Statement,
    StringInterpolationExpr,
    TupleExpr,
    TypeNode,
    UnaryExpr,
    VariableDeclStmt,
    WhileStmt,
)
from .errors import ParseError


class Parser:
    """
    Predictive Recursive-Descent Parser for C--.
    Converts a sequence of tokens into an Abstract Syntax Tree (AST).
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens: list[Token] = tokens
        self.current: int = 0
        self.errors: list[ParseError] = []

    # =====================================================
    # Parser Entry Point
    # =====================================================

    def parse(self) -> Program:
        """Parse all tokens into a Program AST node."""
        statements: list[Statement] = []

        while not self.is_at_end():
            # Skip any stray newlines between statements
            if self.match(TokenType.NEWLINE):
                continue
            try:
                stmt = self.statement()
                if stmt is not None:
                    statements.append(stmt)
            except ParseError:
                self.synchronize()

        return Program(statements=statements)

    # =====================================================
    # Statement Rules
    # =====================================================

    def statement(self) -> Statement:
        """Parse a single statement (compound or simple)."""
        # pub prefix: pub fn ... or pub class ...
        if self.match(TokenType.PUB):
            return self._pub_statement()
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.FROM):
            return self.from_import_statement()
        if self.check(TokenType.FN):
            return self.function_def()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.MATCH):
            return self.match_statement()
        if self.match(TokenType.CLASS):
            return self.class_def()
        if self.match(TokenType.SPEC):
            return self.spec_def()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.BREAK):
            self.consume_statement_end()
            return BreakStmt()
        if self.match(TokenType.CONTINUE):
            self.consume_statement_end()
            return ContinueStmt()

        return self.expression_or_assignment_statement()

    def _pub_statement(self) -> Statement:
        """Handle the 'pub' visibility modifier: pub fn ... or pub class ..."""
        # 'pub' was already consumed; now dispatch to fn or class
        if self.check(TokenType.FN):
            stmt = self.function_def()
            stmt.is_public = True  # type: ignore[attr-defined]
            return stmt
        if self.match(TokenType.CLASS):
            stmt = self.class_def()
            stmt.is_public = True  # type: ignore[attr-defined]
            return stmt
        # 'pub' on anything else is a parse error
        tok = self.peek()
        err = ParseError("Expected 'fn' or 'class' after 'pub'", tok)
        self.errors.append(err)
        raise err

    # ------------------------------------------------------------------
    # Import statements
    # ------------------------------------------------------------------

    def import_statement(self) -> ImportStmt:
        """Parse: import <module> [as <alias>]
           The IMPORT token was already consumed by statement().
        """
        import_tok = self.previous()
        module_parts: list[str] = []
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected module name after 'import'")
        module_parts.append(name_tok.lexeme)
        # Support dotted module paths: import foo.bar.baz
        while self.check(TokenType.DOT):
            self.advance()
            part_tok = self.consume(TokenType.IDENTIFIER, "Expected identifier after '.' in module path")
            module_parts.append(part_tok.lexeme)
        module = ".".join(module_parts)

        alias: str | None = None
        if self.match(TokenType.AS):
            alias_tok = self.consume(TokenType.IDENTIFIER, "Expected alias name after 'as'")
            alias = alias_tok.lexeme

        self.consume_statement_end()
        return ImportStmt(
            line=import_tok.line,
            column=import_tok.column,
            module=module,
            alias=alias,
            symbols=[],
        )

    def from_import_statement(self) -> ImportStmt:
        """Parse: from <module> import <name> [as <alias>] {, <name> [as <alias>]}
                  from <module> import *
           The FROM token was already consumed by statement().
        """
        from_tok = self.previous()
        module_parts: list[str] = []
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected module name after 'from'")
        module_parts.append(name_tok.lexeme)
        while self.check(TokenType.DOT):
            self.advance()
            part_tok = self.consume(TokenType.IDENTIFIER, "Expected identifier after '.' in module path")
            module_parts.append(part_tok.lexeme)
        module = ".".join(module_parts)

        self.consume(TokenType.IMPORT, "Expected 'import' after module name in 'from' import")

        symbols: list[tuple[str, str | None]] = []

        # from module import *
        if self.match(TokenType.MUL):
            symbols.append(("*", None))
        else:
            symbols.append(self._import_symbol())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.NEWLINE) or self.is_at_end():
                    break
                symbols.append(self._import_symbol())

        self.consume_statement_end()
        return ImportStmt(
            line=from_tok.line,
            column=from_tok.column,
            module=module,
            alias=None,
            symbols=symbols,
        )

    def _import_symbol(self) -> tuple[str, str | None]:
        """Parse a single imported symbol with optional alias: name [as alias]."""
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected symbol name in import list")
        alias: str | None = None
        if self.match(TokenType.AS):
            alias_tok = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'")
            alias = alias_tok.lexeme
        return (name_tok.lexeme, alias)

    def function_def(self) -> FunctionDefStmt:
        """Parse a function definition: fn name(params) -> type: Block"""
        fn_tok = self.consume(TokenType.FN, "Expected 'fn'")
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')' after parameter list")

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type()

        body = self.block()
        return FunctionDefStmt(
            line=fn_tok.line,
            column=fn_tok.column,
            name=name_tok.lexeme,
            params=params,
            return_type=return_type,
            body=body,
        )

    def parameter_list(self) -> list[Parameter]:
        """Parse a comma-separated parameter list: param1, param2, ..."""
        params: list[Parameter] = []
        if not self.check(TokenType.RPAREN):
            params.append(self.parameter())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RPAREN):
                    break  # Trailing comma
                params.append(self.parameter())
        return params

    def parameter(self) -> Parameter:
        """Parse a single parameter: name [: Type]"""
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
        type_annot = None
        if self.match(TokenType.COLON):
            type_annot = self.parse_type()
        return Parameter(line=name_tok.line, column=name_tok.column, name=name_tok.lexeme, type_annotation=type_annot)

    def block(self) -> list[Statement]:
        """Parse an indentation-delimited block: : NEWLINE INDENT statements DEDENT"""
        self.consume(TokenType.COLON, "Expected ':' before block")
        while self.match(TokenType.NEWLINE):
            pass
        self.consume(TokenType.INDENT, "Expected indented block")

        statements: list[Statement] = []
        while not self.is_at_end() and not self.check(TokenType.DEDENT):
            if self.match(TokenType.NEWLINE):
                continue
            try:
                stmt = self.statement()
                if stmt is not None:
                    statements.append(stmt)
            except ParseError:
                self.synchronize()

        self.consume(TokenType.DEDENT, "Expected dedent at end of block")
        return statements

    def if_statement(self) -> IfStmt:
        """Parse an if-elif-else statement."""
        start_tok = self.previous()
        condition = self.expression()
        then_branch = self.block()

        elif_branches: list[tuple[Expression, list[Statement]]] = []
        while self.match(TokenType.ELIF):
            elif_cond = self.expression()
            elif_body = self.block()
            elif_branches.append((elif_cond, elif_body))

        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.block()

        return IfStmt(
            line=start_tok.line,
            column=start_tok.column,
            condition=condition,
            then_branch=then_branch,
            elif_branches=elif_branches,
            else_branch=else_branch,
        )

    def while_statement(self) -> WhileStmt:
        """Parse a while loop: while condition: Block"""
        start_tok = self.previous()
        condition = self.expression()
        body = self.block()
        return WhileStmt(line=start_tok.line, column=start_tok.column, condition=condition, body=body)

    def for_statement(self) -> ForStmt:
        """Parse a for loop: for var in iterable: Block"""
        start_tok = self.previous()
        target_tok = self.consume(TokenType.IDENTIFIER, "Expected variable name in for loop")
        self.consume(TokenType.IN, "Expected 'in' in for loop")
        iterable = self.expression()
        body = self.block()
        return ForStmt(
            line=start_tok.line,
            column=start_tok.column,
            target=target_tok.lexeme,
            iterable=iterable,
            body=body,
        )

    def match_statement(self) -> MatchStmt:
        """Parse pattern matching: match expr: NEWLINE INDENT cases DEDENT"""
        start_tok = self.previous()
        subject = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after match expression")
        while self.match(TokenType.NEWLINE):
            pass
        self.consume(TokenType.INDENT, "Expected indented match cases")

        cases: list[CaseClause] = []
        while not self.is_at_end() and not self.check(TokenType.DEDENT):
            if self.match(TokenType.NEWLINE):
                continue
            cases.append(self.case_clause())

        self.consume(TokenType.DEDENT, "Expected dedent at end of match block")
        return MatchStmt(line=start_tok.line, column=start_tok.column, subject=subject, cases=cases)

    def case_clause(self) -> CaseClause:
        """Parse a single match arm: case pattern [if guard] (Block | => stmt)"""
        case_tok = self.consume(TokenType.CASE, "Expected 'case'")
        pattern = self.logical_or_expr()
        guard = None
        if self.match(TokenType.IF):
            guard = self.expression()

        if self.match(TokenType.FAT_ARROW):
            body = [self.statement()]
        else:
            body = self.block()

        return CaseClause(line=case_tok.line, column=case_tok.column, pattern=pattern, guard=guard, body=body)

    def class_def(self) -> ClassDefStmt:
        """Parse a class definition: class Name [(Bases)]: Block"""
        class_tok = self.previous()
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected class name")

        heritage: list[TypeNode] = []
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                heritage.append(self.parse_type())
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RPAREN):
                        break
                    heritage.append(self.parse_type())
            self.consume(TokenType.RPAREN, "Expected ')' after base classes")

        self.consume(TokenType.COLON, "Expected ':' before class body")
        while self.match(TokenType.NEWLINE):
            pass
        self.consume(TokenType.INDENT, "Expected indented class body")

        members: list[ClassMember] = []
        while not self.is_at_end() and not self.check(TokenType.DEDENT):
            if self.match(TokenType.NEWLINE):
                continue
            visibility = "+"
            if self.match(TokenType.PLUS):
                visibility = "+"
            elif self.match(TokenType.MINUS):
                visibility = "-"

            if self.check(TokenType.FN):
                member_def = self.function_def()
            else:
                member_def = self.field_decl()
            members.append(ClassMember(visibility=visibility, definition=member_def))

        self.consume(TokenType.DEDENT, "Expected dedent at end of class body")
        return ClassDefStmt(
            line=class_tok.line,
            column=class_tok.column,
            name=name_tok.lexeme,
            heritage=heritage,
            members=members,
        )

    def field_decl(self) -> FieldDecl:
        """Parse a class field declaration: name: Type [= expr] NEWLINE"""
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected field name")
        self.consume(TokenType.COLON, "Expected ':' after field name")
        type_annot = self.parse_type()
        init_val = None
        if self.match(TokenType.ASSIGN):
            init_val = self.expression()
        self.consume_statement_end()
        return FieldDecl(
            line=name_tok.line,
            column=name_tok.column,
            name=name_tok.lexeme,
            type_annotation=type_annot,
            init_value=init_val,
        )

    def spec_def(self) -> SpecDefStmt:
        """Parse a spec definition: spec Name: Block"""
        spec_tok = self.previous()
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected spec name")
        self.consume(TokenType.COLON, "Expected ':' before spec body")
        while self.match(TokenType.NEWLINE):
            pass
        self.consume(TokenType.INDENT, "Expected indented spec body")

        members: list[Statement] = []
        while not self.is_at_end() and not self.check(TokenType.DEDENT):
            if self.match(TokenType.NEWLINE):
                continue
            if self.match(TokenType.FN):
                fn_tok = self.previous()
                m_name = self.consume(TokenType.IDENTIFIER, "Expected function name in spec")
                self.consume(TokenType.LPAREN, "Expected '('")
                params = self.parameter_list()
                self.consume(TokenType.RPAREN, "Expected ')'")
                ret_type = None
                if self.match(TokenType.ARROW):
                    ret_type = self.parse_type()
                self.consume_statement_end()
                members.append(
                    FunctionDefStmt(
                        line=fn_tok.line,
                        column=fn_tok.column,
                        name=m_name.lexeme,
                        params=params,
                        return_type=ret_type,
                        body=[],
                    )
                )
            else:
                f_name = self.consume(TokenType.IDENTIFIER, "Expected field name in spec")
                self.consume(TokenType.COLON, "Expected ':'")
                f_type = self.parse_type()
                self.consume_statement_end()
                members.append(FieldDecl(name=f_name.lexeme, type_annotation=f_type))

        self.consume(TokenType.DEDENT, "Expected dedent at end of spec body")
        return SpecDefStmt(line=spec_tok.line, column=spec_tok.column, name=name_tok.lexeme, members=members)

    def return_statement(self) -> ReturnStmt:
        """Parse a return statement: return [expr] NEWLINE"""
        ret_tok = self.previous()
        value = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.DEDENT) and not self.is_at_end():
            value = self.expression()
        self.consume_statement_end()
        return ReturnStmt(line=ret_tok.line, column=ret_tok.column, value=value)

    def expression_or_assignment_statement(self) -> Statement:
        """
        Disambiguate and parse:
        1. Explicit typed declaration: name: Type = expr
        2. Assignment: target = expr
        3. Compound assignment: target += expr
        4. Expression statement: expr
        """
        # Lookahead check for typed variable declaration: IDENTIFIER ':' Type '='
        if (
            self.check(TokenType.IDENTIFIER)
            and self.peek(1).type == TokenType.COLON
            and self.peek(2).type != TokenType.ASSIGN
        ):
            name_tok = self.advance()
            self.consume(TokenType.COLON, "Expected ':' in variable declaration")
            type_annot = self.parse_type()
            value = None
            if self.match(TokenType.ASSIGN):
                value = self.expression()
            self.consume_statement_end()
            return VariableDeclStmt(
                line=name_tok.line,
                column=name_tok.column,
                name=name_tok.lexeme,
                type_annotation=type_annot,
                value=value,
            )

        expr = self.expression()

        # Assignment: target = value
        if self.match(TokenType.ASSIGN):
            value = self.expression()
            self.consume_statement_end()
            return AssignmentStmt(line=expr.line, column=expr.column, target=expr, value=value)

        # Compound assignment: target += value, etc.
        if self.match(
            TokenType.PLUS_EQ,
            TokenType.MINUS_EQ,
            TokenType.MUL_EQ,
            TokenType.DIV_EQ,
            TokenType.MOD_EQ,
        ):
            op = self.previous()
            value = self.expression()
            self.consume_statement_end()
            return AugmentedAssignStmt(line=expr.line, column=expr.column, target=expr, op=op, value=value)

        # Standalone expression statement
        self.consume_statement_end()
        return ExpressionStmt(line=expr.line, column=expr.column, expression=expr)

    def consume_statement_end(self) -> None:
        """Consume a terminating newline or verify statement boundary at EOF/DEDENT."""
        if not self.is_at_end() and not self.check(TokenType.DEDENT):
            self.consume(TokenType.NEWLINE, "Expected newline after statement")

    # =====================================================
    # Expressions Hierarchy (Lowest to Highest Precedence)
    # =====================================================

    def expression(self) -> Expression:
        """Level 1: Expression entry point (Conditional expression)."""
        return self.conditional_expr()

    def conditional_expr(self) -> Expression:
        """Level 2: Ternary / Conditional: val if cond else fallback"""
        expr = self.logical_or_expr()
        if self.match(TokenType.IF):
            condition = self.logical_or_expr()
            self.consume(TokenType.ELSE, "Expected 'else' in conditional expression")
            false_expr = self.conditional_expr()
            return ConditionalExpr(
                line=expr.line,
                column=expr.column,
                condition=condition,
                true_expr=expr,
                false_expr=false_expr,
            )
        return expr

    def logical_or_expr(self) -> Expression:
        """Level 3: Logical OR: expr or expr"""
        expr = self.logical_and_expr()
        while self.match(TokenType.OR):
            op = self.previous()
            right = self.logical_and_expr()
            expr = BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def logical_and_expr(self) -> Expression:
        """Level 4: Logical AND: expr and expr"""
        expr = self.logical_not_expr()
        while self.match(TokenType.AND):
            op = self.previous()
            right = self.logical_not_expr()
            expr = BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def logical_not_expr(self) -> Expression:
        """Level 5: Logical NOT: not expr"""
        if self.match(TokenType.NOT):
            op = self.previous()
            operand = self.logical_not_expr()
            return UnaryExpr(line=op.line, column=op.column, op=op, operand=operand)
        return self.comparison_expr()

    def comparison_expr(self) -> Expression:
        """Level 6: Comparison: ==, !=, <, <=, >, >="""
        expr = self.range_expr()
        while self.match(
            TokenType.EQ,
            TokenType.NOT_EQ,
            TokenType.LT,
            TokenType.LT_EQ,
            TokenType.GT,
            TokenType.GT_EQ,
        ):
            op = self.previous()
            right = self.range_expr()
            expr = BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def range_expr(self) -> Expression:
        """Level 7: Range: 0..10"""
        expr = self.additive_expr()
        if self.match(TokenType.RANGE):
            op = self.previous()
            right = self.additive_expr()
            return BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def additive_expr(self) -> Expression:
        """Level 8: Additive: +, -"""
        expr = self.multiplicative_expr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous()
            right = self.multiplicative_expr()
            expr = BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def multiplicative_expr(self) -> Expression:
        """Level 9: Multiplicative: *, /, //, %"""
        expr = self.unary_expr()
        while self.match(TokenType.MUL, TokenType.DIV, TokenType.FLOOR_DIV, TokenType.MOD):
            op = self.previous()
            right = self.unary_expr()
            expr = BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def unary_expr(self) -> Expression:
        """Level 10: Unary: +, -"""
        if self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous()
            operand = self.unary_expr()
            return UnaryExpr(line=op.line, column=op.column, op=op, operand=operand)
        return self.power_expr()

    def power_expr(self) -> Expression:
        """Level 11: Exponentiation (right-associative): a ** b"""
        expr = self.postfix_expr()
        if self.match(TokenType.POW):
            op = self.previous()
            right = self.unary_expr()
            return BinaryExpr(line=expr.line, column=expr.column, left=expr, op=op, right=right)
        return expr

    def postfix_expr(self) -> Expression:
        """Level 12: Postfix operations: calls (), indexing [], member access ."""
        expr = self.primary_expr()
        while True:
            if self.match(TokenType.LPAREN):
                args = self.argument_list()
                self.consume(TokenType.RPAREN, "Expected ')' after argument list")
                expr = CallExpr(line=expr.line, column=expr.column, callee=expr, arguments=args)
            elif self.match(TokenType.LBRACKET):
                index_or_slice = self.slice_or_index()
                self.consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExpr(line=expr.line, column=expr.column, target=expr, index=index_or_slice)
            elif self.match(TokenType.DOT):
                member_tok = self.consume(TokenType.IDENTIFIER, "Expected member name after '.'")
                expr = MemberAccessExpr(
                    line=expr.line,
                    column=expr.column,
                    target=expr,
                    member=member_tok.lexeme,
                )
            else:
                break
        return expr

    def argument_list(self) -> list[Expression]:
        """Parse arguments: expr, expr, ..."""
        args: list[Expression] = []
        if not self.check(TokenType.RPAREN):
            args.append(self.expression())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RPAREN):
                    break
                args.append(self.expression())
        return args

    def slice_or_index(self) -> Expression:
        """Parse indexing or slicing: [idx] or [start:stop:step]"""
        if self.match(TokenType.COLON):
            # Colon first: [:stop]
            stop = None
            step = None
            if not self.check(TokenType.COLON) and not self.check(TokenType.RBRACKET):
                stop = self.expression()
            if self.match(TokenType.COLON):
                if not self.check(TokenType.RBRACKET):
                    step = self.expression()
            return SliceExpr(start=None, stop=stop, step=step)

        start = self.expression()
        if self.match(TokenType.COLON):
            stop = None
            step = None
            if not self.check(TokenType.COLON) and not self.check(TokenType.RBRACKET):
                stop = self.expression()
            if self.match(TokenType.COLON):
                if not self.check(TokenType.RBRACKET):
                    step = self.expression()
            return SliceExpr(start=start, stop=stop, step=step)

        return start

    # =====================================================
    # Primary Expressions & Literals
    # =====================================================

    def primary_expr(self) -> Expression:
        """Level 13: Primary expressions, literals, grouped expressions, collections."""
        # 1. Literals
        if self.match(TokenType.INTEGER):
            tok = self.previous()
            return LiteralExpr(line=tok.line, column=tok.column, value=int(tok.lexeme), raw=tok.lexeme)

        if self.match(TokenType.FLOAT):
            tok = self.previous()
            return LiteralExpr(line=tok.line, column=tok.column, value=float(tok.lexeme), raw=tok.lexeme)

        if self.match(TokenType.BOOL):
            tok = self.previous()
            val = tok.lexeme.lower() == "true"
            return LiteralExpr(line=tok.line, column=tok.column, value=val, raw=tok.lexeme)

        if self.match(TokenType.NONE):
            tok = self.previous()
            return LiteralExpr(line=tok.line, column=tok.column, value=None, raw=tok.lexeme)

        # 2. Strings & String Interpolation
        if self.match(TokenType.STRING):
            first_tok = self.previous()
            # Check if this string token is part of a backtick interpolation chain
            if self.check(TokenType.LBRACE):
                parts: list[Expression | str] = [first_tok.lexeme]
                while self.match(TokenType.LBRACE):
                    parts.append(self.expression())
                    self.consume(TokenType.RBRACE, "Expected '}' in string interpolation")
                    if self.match(TokenType.STRING):
                        parts.append(self.previous().lexeme)
                return StringInterpolationExpr(line=first_tok.line, column=first_tok.column, parts=parts)

            # Normal string literal (single quote, double quote, or backtick without interpolation)
            return LiteralExpr(
                line=first_tok.line,
                column=first_tok.column,
                value=first_tok.lexeme[1:-1],
                raw=first_tok.lexeme,
            )

        # 3. Arrow Function: fn(params): type => expr
        if self.check(TokenType.FN) and self.peek(1).type == TokenType.LPAREN:
            return self.arrow_function()

        # 4. Built-ins or Identifiers
        if self.match(TokenType.PRINT, TokenType.INPUT, TokenType.IDENTIFIER):
            tok = self.previous()
            return IdentifierExpr(line=tok.line, column=tok.column, name=tok.lexeme)

        # 5. Grouped expression or Tuple literal: (expr) or (a, b)
        if self.match(TokenType.LPAREN):
            start_tok = self.previous()
            if self.match(TokenType.RPAREN):
                return TupleExpr(line=start_tok.line, column=start_tok.column, elements=[])
            expr = self.expression()
            if self.match(TokenType.COMMA):
                elements = [expr]
                if not self.check(TokenType.RPAREN):
                    elements.append(self.expression())
                    while self.match(TokenType.COMMA):
                        if self.check(TokenType.RPAREN):
                            break
                        elements.append(self.expression())
                self.consume(TokenType.RPAREN, "Expected ')' after tuple elements")
                return TupleExpr(line=start_tok.line, column=start_tok.column, elements=elements)
            self.consume(TokenType.RPAREN, "Expected ')' after grouped expression")
            return expr

        # 6. List Literal: [1, 2, 3]
        if self.match(TokenType.LBRACKET):
            start_tok = self.previous()
            elements: list[Expression] = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACKET):
                        break
                    elements.append(self.expression())
            self.consume(TokenType.RBRACKET, "Expected ']' after list elements")
            return ListExpr(line=start_tok.line, column=start_tok.column, elements=elements)

        # 7. Dict Literal: {"key": value, ...}
        if self.match(TokenType.LBRACE):
            start_tok = self.previous()
            pairs: list[tuple[Expression, Expression]] = []
            if not self.check(TokenType.RBRACE):
                key = self.expression()
                self.consume(TokenType.COLON, "Expected ':' in key-value pair")
                val = self.expression()
                pairs.append((key, val))
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACE):
                        break
                    key = self.expression()
                    self.consume(TokenType.COLON, "Expected ':' in key-value pair")
                    val = self.expression()
                    pairs.append((key, val))
            self.consume(TokenType.RBRACE, "Expected '}' after dict pairs")
            return DictExpr(line=start_tok.line, column=start_tok.column, pairs=pairs)

        # Syntax Error
        tok = self.peek()
        err = ParseError(f"Unexpected token in expression: {tok.type.name}", tok)
        self.errors.append(err)
        raise err

    def arrow_function(self) -> ArrowFunctionExpr:
        """Parse an arrow function: fn(params): type => expr"""
        fn_tok = self.consume(TokenType.FN, "Expected 'fn'")
        self.consume(TokenType.LPAREN, "Expected '(' after 'fn'")
        params = self.parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')' after parameter list")

        return_type = None
        if self.match(TokenType.COLON):
            return_type = self.parse_type()

        self.consume(TokenType.FAT_ARROW, "Expected '=>' in arrow function")
        body = self.expression()
        return ArrowFunctionExpr(
            line=fn_tok.line,
            column=fn_tok.column,
            params=params,
            return_type=return_type,
            body=body,
        )

    # =====================================================
    # Type Parser
    # =====================================================

    def parse_type(self) -> TypeNode:
        """Parse a type expression: TypeName[TypeArg1, TypeArg2]"""
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected type name")
        type_args: list[TypeNode] = []
        if self.match(TokenType.LBRACKET):
            type_args.append(self.parse_type())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RBRACKET):
                    break
                type_args.append(self.parse_type())
            self.consume(TokenType.RBRACKET, "Expected ']' after generic type arguments")
        return TypeNode(
            line=name_tok.line,
            column=name_tok.column,
            name=name_tok.lexeme,
            type_args=type_args,
        )

    # =====================================================
    # Helper & Lookahead Methods
    # =====================================================

    def is_at_end(self) -> bool:
        """Check if the parser has reached EOF."""
        return self.peek().type == TokenType.EOF

    def peek(self, offset: int = 0) -> Token:
        """Inspect a token at the current position + offset without consuming it."""
        idx = min(self.current + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def check(self, type: TokenType) -> bool:
        """Check if the current token matches the expected type."""
        if self.is_at_end():
            return False
        return self.peek().type == type

    def advance(self) -> Token:
        """Consume and return the current token."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def match(self, *types: TokenType) -> bool:
        """Consume the current token if it matches any of the given types."""
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, type: TokenType, message: str) -> Token:
        """Consume the expected token or raise a ParseError."""
        if self.check(type):
            return self.advance()
        err = ParseError(message, self.peek())
        self.errors.append(err)
        raise err

    def synchronize(self) -> None:
        """Panic-mode recovery: skip tokens until reaching a statement boundary."""
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.NEWLINE:
                return

            if self.peek().type in (
                TokenType.FN,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.MATCH,
                TokenType.CLASS,
                TokenType.SPEC,
                TokenType.RETURN,
                TokenType.BREAK,
                TokenType.CONTINUE,
                TokenType.DEDENT,
            ):
                return

            self.advance()
