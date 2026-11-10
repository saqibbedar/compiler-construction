# C-- Context-Free Grammar (CFG) Specification

## 1. Overview & Formal Definition

This document specifies the formal **Context-Free Grammar (CFG)** for the **C--** programming language.

Formally, the grammar is defined as a 4-tuple:
$$G = (V, \Sigma, R, S)$$

- **$V$ (Non-Terminals)**: Syntactic variables representing language constructs (e.g., `Program`, `Statement`, `Expression`). In the upcoming **Recursive-Descent Parser**, every non-terminal $A \in V$ corresponds directly to a parsing method `parse_A()`.
- **$\Sigma$ (Terminals)**: The lexical tokens emitted by the C-- Lexer (e.g., `IDENTIFIER`, `INTEGER`, `IF`, `COLON`, `NEWLINE`, `INDENT`, `DEDENT`, `EOF`).
- **$R$ (Production Rules)**: Finite set of rewrite rules of the form $A \to \alpha$, where $A \in V$ and $\alpha \in (V \cup \Sigma)^*$.
- **$S$ (Start Symbol)**: The initial non-terminal `Program`.
- **$\varepsilon$**: Represents the empty string (epsilon transition).

---

## 2. Notation & Design Principles

1. **Terminals**: Written in `UPPERCASE_BOLD` or exact punctuation (matching `TokenType` in `src/lexer/tokens.py`), e.g., `FN`, `COLON`, `NEWLINE`, `INDENT`, `DEDENT`.
2. **Non-Terminals**: Written in `CamelCase` or `PascalCase`, e.g., `StatementList`, `BinaryExpr`, `PrimaryExpr`.
3. **Pure CFG Notation**: Rules use standard production syntax (`A -> alpha | beta`). Repetition and optional elements are expressed purely through **recursion** and **$\varepsilon$**, avoiding regex shorthands (which will be featured in the subsequent BNF/EBNF versions).
4. **No Left Recursion**: All left-recursive productions have been eliminated and transformed into right-recursive forms ($A \to \beta A'$) so that the grammar can be implemented directly by a **predictive recursive-descent parser** without infinite recursion.
5. **Strict Precedence Hierarchy**: The expression grammar encodes exact operator precedence and associativity levels natively into non-terminal strata.

---

## 3. CFG Production Rules

### 3.1 Program & High-Level Structure

```
Program                 -> StatementList EOF

StatementList           -> Statement StatementList
                         | ε

Statement               -> CompoundStatement
                         | SimpleStatement

CompoundStatement       -> FunctionDef
                         | IfStatement
                         | WhileStatement
                         | ForStatement
                         | MatchStatement
                         | ClassDef
                         | SpecDef

SimpleStatement         -> SmallStatement NEWLINE
                         | NEWLINE

SmallStatement          -> VariableDeclOrAssign
                         | ReturnStatement
                         | BreakStatement
                         | ContinueStatement
                         | ImportStatement
                         | ExpressionStatement

Block                   -> COLON NEWLINE INDENT StatementList DEDENT
```

---

### 3.2 Declarations

#### Function Definition
```
FunctionDef             -> FN IDENTIFIER LPAREN ParameterListOpt RPAREN ReturnTypeOpt Block

ParameterListOpt        -> ParameterList
                         | ε

ParameterList           -> Parameter ParameterListTail

ParameterListTail       -> COMMA Parameter ParameterListTail
                         | COMMA
                         | ε

Parameter               -> IDENTIFIER TypeAnnotationOpt

TypeAnnotationOpt       -> COLON Type
                         | ε

ReturnTypeOpt           -> ARROW Type
                         | ε
```

#### Class & Spec Definition
```
ClassDef                -> CLASS IDENTIFIER ClassHeritageOpt COLON NEWLINE INDENT ClassBody DEDENT

ClassHeritageOpt        -> LPAREN TypeList RPAREN
                         | ε

ClassBody               -> ClassMember ClassBody
                         | ε

ClassMember             -> MemberVisibilityOpt MemberDefinition

MemberVisibilityOpt     -> PLUS
                         | MINUS
                         | ε

MemberDefinition        -> FunctionDef
                         | FieldDecl

FieldDecl               -> IDENTIFIER COLON Type FieldInitOpt NEWLINE

FieldInitOpt            -> ASSIGN Expression
                         | ε

SpecDef                 -> SPEC IDENTIFIER COLON NEWLINE INDENT SpecBody DEDENT

SpecBody                -> SpecMember SpecBody
                         | ε

SpecMember              -> FN IDENTIFIER LPAREN ParameterListOpt RPAREN ReturnTypeOpt NEWLINE
                         | IDENTIFIER COLON Type NEWLINE
```

---

### 3.3 Variable Declarations & Assignments

```
VariableDeclOrAssign    -> Target AssignRest

AssignRest              -> COLON Type ASSIGN Expression
                         | ASSIGN Expression
                         | CompoundAssignOp Expression

CompoundAssignOp        -> PLUS_EQ
                         | MINUS_EQ
                         | MUL_EQ
                         | DIV_EQ
                         | MOD_EQ

Target                  -> IDENTIFIER TargetSuffixList

TargetSuffixList        -> TargetSuffix TargetSuffixList
                         | ε

TargetSuffix            -> DOT IDENTIFIER
                         | LBRACKET Expression RBRACKET
```

---

### 3.4 Control Flow Statements

#### If / Elif / Else
```
IfStatement             -> IF Expression Block ElifList ElseOpt

ElifList                -> ElifClause ElifList
                         | ε

ElifClause              -> ELIF Expression Block

ElseOpt                 -> ELSE Block
                         | ε
```

#### Loops (While & For)
```
WhileStatement          -> WHILE Expression Block

ForStatement            -> FOR ForTarget IN Expression Block

ForTarget               -> IDENTIFIER
                         | LPAREN TargetList RPAREN
                         | LBRACKET TargetList RBRACKET

TargetList              -> IDENTIFIER TargetListTail

TargetListTail          -> COMMA IDENTIFIER TargetListTail
                         | COMMA
                         | ε
```

#### Match / Case
```
MatchStatement          -> MATCH Expression COLON NEWLINE INDENT CaseList DEDENT

CaseList                -> CaseClause CaseList
                         | ε

CaseClause              -> CASE Pattern CaseGuardOpt CaseBody

CaseGuardOpt            -> IF Expression
                         | ε

CaseBody                -> Block
                         | FAT_ARROW SimpleStatement

Pattern                 -> Literal
                         | IDENTIFIER
                         | PatternTuple
                         | PatternList

PatternTuple            -> LPAREN PatternElementsOpt RPAREN

PatternList             -> LBRACKET PatternElementsOpt RBRACKET

PatternElementsOpt      -> Pattern PatternElementsTail
                         | ε

PatternElementsTail     -> COMMA Pattern PatternElementsTail
                         | COMMA
                         | ε
```

---

### 3.5 Simple Statements

```
ReturnStatement         -> RETURN ExpressionOpt

ExpressionOpt           -> Expression
                         | ε

BreakStatement          -> BREAK

ContinueStatement       -> CONTINUE

ExpressionStatement     -> Expression

ImportStatement         -> IMPORT DottedName ImportAliasOpt
                         | FROM DottedName IMPORT ImportSymbols

ImportAliasOpt          -> AS IDENTIFIER
                         | ε

ImportSymbols           -> ImportSymbol ImportSymbolsTail

ImportSymbolsTail       -> COMMA ImportSymbol ImportSymbolsTail
                         | COMMA
                         | ε

ImportSymbol            -> IDENTIFIER ImportAliasOpt

DottedName              -> IDENTIFIER DottedNameTail

DottedNameTail          -> DOT IDENTIFIER DottedNameTail
                         | ε
```

---

### 3.6 Expressions & Operator Precedence (Unambiguous & Non-Left-Recursive)

The expression rules are arranged from lowest precedence to highest precedence. Left-associative binary operators are transformed using tail non-terminals ($A \to B A'$) to eliminate left-recursion.

```
Expression              -> ConditionalExpr

# 1. Conditional (Ternary) Expression: val if cond else fallback
ConditionalExpr         -> LogicalOrExpr ConditionalTail

ConditionalTail         -> IF LogicalOrExpr ELSE ConditionalExpr
                         | ε

# 2. Logical OR (or)
LogicalOrExpr           -> LogicalAndExpr LogicalOrTail

LogicalOrTail           -> OR LogicalAndExpr LogicalOrTail
                         | ε

# 3. Logical AND (and)
LogicalAndExpr          -> LogicalNotExpr LogicalAndTail

LogicalAndTail          -> AND LogicalNotExpr LogicalAndTail
                         | ε

# 4. Logical NOT (not)
LogicalNotExpr          -> NOT LogicalNotExpr
                         | ComparisonExpr

# 5. Relational & Equality Comparisons (==, !=, <, <=, >, >=)
ComparisonExpr          -> RangeExpr ComparisonTail

ComparisonTail          -> ComparisonOp RangeExpr ComparisonTail
                         | ε

ComparisonOp            -> EQ
                         | NOT_EQ
                         | LT
                         | LT_EQ
                         | GT
                         | GT_EQ

# 6. Range (..)
RangeExpr               -> AdditiveExpr RangeTail

RangeTail               -> RANGE AdditiveExpr
                         | ε

# 7. Addition and Subtraction (+, -)
AdditiveExpr            -> MultiplicativeExpr AdditiveTail

AdditiveTail            -> AdditiveOp MultiplicativeExpr AdditiveTail
                         | ε

AdditiveOp              -> PLUS
                         | MINUS

# 8. Multiplication, Division, Floor Division, Modulo (*, /, //, %)
MultiplicativeExpr      -> UnaryExpr MultiplicativeTail

MultiplicativeTail      -> MultiplicativeOp UnaryExpr MultiplicativeTail
                         | ε

MultiplicativeOp        -> MUL
                         | DIV
                         | FLOOR_DIV
                         | MOD

# 9. Unary Prefix (+, -)
UnaryExpr               -> PLUS UnaryExpr
                         | MINUS UnaryExpr
                         | PowerExpr

# 10. Exponentiation / Power (**) [Right-Associative: 2 ** 3 ** 4 == 2 ** (3 ** 4)]
PowerExpr               -> PostfixExpr PowerTail

PowerTail               -> POW UnaryExpr
                         | ε

# 11. Postfix Operations (Calls, Indexing, Slicing, Member Access)
PostfixExpr             -> PrimaryExpr PostfixTail

PostfixTail             -> PostfixOp PostfixTail
                         | ε

PostfixOp               -> CallSuffix
                         | IndexOrSliceSuffix
                         | MemberAccessSuffix

CallSuffix              -> LPAREN ArgumentListOpt RPAREN

ArgumentListOpt         -> ArgumentList
                         | ε

ArgumentList            -> Argument ArgumentListTail

ArgumentListTail        -> COMMA Argument ArgumentListTail
                         | COMMA
                         | ε

Argument                -> Expression

IndexOrSliceSuffix      -> LBRACKET SliceContent RBRACKET

SliceContent            -> Expression SliceContentTail
                         | COLON SliceEndOpt SliceStepOpt

SliceContentTail        -> COLON SliceEndOpt SliceStepOpt
                         | ε

SliceEndOpt             -> Expression
                         | ε

SliceStepOpt            -> COLON ExpressionOpt
                         | ε

MemberAccessSuffix      -> DOT IDENTIFIER
```

---

### 3.7 Primary Expressions, Literals & Arrow Functions

```
PrimaryExpr             -> Literal
                         | StringInterpolation
                         | ArrowFunction
                         | IDENTIFIER
                         | GroupedOrTupleExpr
                         | ListLiteral
                         | DictLiteral

# Arrow Function: fn(a: int, b: int): int => a + b
ArrowFunction           -> FN LPAREN ParameterListOpt RPAREN ArrowReturnTypeOpt FAT_ARROW Expression

ArrowReturnTypeOpt      -> COLON Type
                         | ε

# Literals
Literal                 -> INTEGER
                         | FLOAT
                         | STRING
                         | BOOL
                         | NONE

# Backtick String Interpolation: `Hello, {name}`
# The lexer produces: STRING("{chunk}") LBRACE Expression RBRACE STRING("{chunk}")
StringInterpolation     -> STRING StringInterpolationTail

StringInterpolationTail -> LBRACE Expression RBRACE STRING StringInterpolationTail
                         | ε

# Parenthesized Expression or Tuple Literal
GroupedOrTupleExpr      -> LPAREN GroupedOrTupleBody RPAREN

GroupedOrTupleBody      -> Expression GroupedOrTupleTail
                         | ε

GroupedOrTupleTail      -> COMMA ExpressionListOpt
                         | ε

ExpressionListOpt       -> ExpressionList
                         | ε

ExpressionList          -> Expression ExpressionListTail

ExpressionListTail      -> COMMA Expression ExpressionListTail
                         | COMMA
                         | ε

# Collection Literals
ListLiteral             -> LBRACKET ExpressionListOpt RBRACKET

DictLiteral             -> LBRACE KeyValueListOpt RBRACE

KeyValueListOpt         -> KeyValueList
                         | ε

KeyValueList            -> KeyValuePair KeyValueListTail

KeyValueListTail        -> COMMA KeyValuePair KeyValueListTail
                         | COMMA
                         | ε

KeyValuePair            -> Expression COLON Expression
```

---

### 3.8 Type System Expressions

```
Type                    -> IDENTIFIER TypeArgumentsOpt

TypeArgumentsOpt        -> LBRACKET TypeList RBRACKET
                         | ε

TypeList                -> Type TypeListTail

TypeListTail            -> COMMA Type TypeListTail
                         | COMMA
                         | ε
```

---

## 4. Terminal Symbols Mapping

The table below maps the CFG terminal symbols to their corresponding `TokenType` in `src/lexer/tokens.py`:

| CFG Terminal | Lexer Token | Lexeme / Description |
| :--- | :--- | :--- |
| `IDENTIFIER` | `TokenType.IDENTIFIER` | Variable/function names (`foo`, `greet`) |
| `INTEGER` | `TokenType.INTEGER` | Integer literals (`42`, `100`) |
| `FLOAT` | `TokenType.FLOAT` | Float literals (`3.14`, `1e9`) |
| `STRING` | `TokenType.STRING` | Double/single-quoted or backtick chunk |
| `BOOL` | `TokenType.BOOL` | `true`, `false`, `True`, `False` |
| `NONE` | `TokenType.NONE` | `None`, `none` |
| `NEWLINE` | `TokenType.NEWLINE` | Logical statement boundary |
| `INDENT` | `TokenType.INDENT` | Block entry (4 spaces) |
| `DEDENT` | `TokenType.DEDENT` | Block exit |
| `EOF` | `TokenType.EOF` | End of source file |
| `FN` | `TokenType.FN` | `fn` keyword |
| `IF` | `TokenType.IF` | `if` keyword |
| `ELIF` | `TokenType.ELIF` | `elif` keyword |
| `ELSE` | `TokenType.ELSE` | `else` keyword |
| `WHILE` | `TokenType.WHILE` | `while` keyword |
| `FOR` | `TokenType.FOR` | `for` keyword |
| `IN` | `TokenType.IN` | `in` keyword |
| `MATCH` | `TokenType.MATCH` | `match` keyword |
| `CASE` | `TokenType.CASE` | `case` keyword |
| `RETURN` | `TokenType.RETURN` | `return` keyword |
| `BREAK` | `TokenType.BREAK` | `break` keyword |
| `CONTINUE` | `TokenType.CONTINUE` | `continue` keyword |
| `IMPORT` | `TokenType.IMPORT` | `import` keyword |
| `FROM` | `TokenType.FROM` | `from` keyword |
| `AS` | `TokenType.AS` | `as` keyword |
| `PUB` | `TokenType.PUB` | `pub` keyword |
| `CLASS` | `TokenType.CLASS` | `class` keyword |
| `SPEC` | `TokenType.SPEC` | `spec` keyword |
| `PLUS`, `MINUS` | `TokenType.PLUS`, `MINUS` | `+`, `-` |
| `MUL`, `DIV` | `TokenType.MUL`, `DIV` | `*`, `/` |
| `FLOOR_DIV`, `MOD` | `TokenType.FLOOR_DIV`, `MOD` | `//`, `%` |
| `POW` | `TokenType.POW` | `**` |
| `EQ`, `NOT_EQ` | `TokenType.EQ`, `NOT_EQ` | `==`, `!=` |
| `LT`, `LT_EQ`, `GT`, `GT_EQ` | `TokenType.LT`, `LT_EQ`, `GT`, `GT_EQ` | `<`, `<=`, `>`, `>=` |
| `AND`, `OR`, `NOT` | `TokenType.AND`, `OR`, `NOT` | `and`, `or`, `not` |
| `ASSIGN` | `TokenType.ASSIGN` | `=` |
| `PLUS_EQ`, `MINUS_EQ`, etc. | `TokenType.PLUS_EQ`, etc. | `+=`, `-=`, `*=`, `/=`, `%=` |
| `RANGE` | `TokenType.RANGE` | `..` |
| `ARROW` | `TokenType.ARROW` | `->` (Function return type) |
| `FAT_ARROW` | `TokenType.FAT_ARROW` | `=>` (Arrow function / match arm) |
| `LPAREN`, `RPAREN` | `TokenType.LPAREN`, `RPAREN` | `(`, `)` |
| `LBRACKET`, `RBRACKET` | `TokenType.LBRACKET`, `RBRACKET` | `[`, `]` |
| `LBRACE`, `RBRACE` | `TokenType.LBRACE`, `RBRACE` | `{`, `}` |
| `COLON`, `COMMA`, `DOT` | `TokenType.COLON`, `COMMA`, `DOT` | `:`, `,`, `.` |

---

## 5. Parser Architecture Alignment: Recursive Descent

In a **Recursive-Descent Parser**, every non-terminal symbol $A$ translates directly into a Python method on the `Parser` class:

```python
class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens: list[Token] = tokens
        self.current: int = 0

    # Non-Terminal: Program
    def parse_program(self) -> ProgramNode:
        statements = self.parse_statement_list()
        self.consume(TokenType.EOF, "Expected EOF")
        return ProgramNode(statements=statements)

    # Non-Terminal: StatementList
    def parse_statement_list(self) -> list[StatementNode]:
        statements: list[StatementNode] = []
        while not self.is_at_end() and self.peek().type != TokenType.DEDENT:
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return statements

    # Non-Terminal: Expression
    def parse_expression(self) -> ExpressionNode:
        return self.parse_conditional_expr()
```

### Note on Parser Architecture: Two-Pass vs One-Pass
- **Two-Pass Architecture (Recommended & Standard for Python/C-- compilers)**:
  1. **Pass 1 (Lexing)**: `Lexer(source).scan_tokens()` transforms raw characters into a complete `list[Token]`. This enables looking ahead (`peek()`, `peek(2)`), backtracking if needed, and cleanly isolating indentation logic.
  2. **Pass 2 (Parsing)**: `Parser(tokens).parse()` consumes the token list and constructs the **Abstract Syntax Tree (AST)**.
- **One-Pass Architecture (Streaming)**:
  The lexer yields tokens on demand (`next_token()`). While memory-efficient for 1970s compilers, a two-pass approach is significantly easier to debug, test, and maintain, especially given modern memory sizes and Python's object model.
