# C-- Extended Backus-Naur Form (EBNF) Specification

## 1. Overview & Conventions

This document specifies the **Extended Backus-Naur Form (EBNF)** for the **C--** programming language.

While pure CFG and BNF use recursive non-terminals to represent repetition and optionality, EBNF introduces standard meta-notations that make the grammar concise, readable, and **directly mappable to recursive-descent parsing code**:

| EBNF Construct | Notation | Recursive-Descent Parser Implementation |
| :--- | :--- | :--- |
| **Optional** | `[ α ]` | `if self.check(...) : ...` |
| **Repetition (0 or more)** | `{ α }` | `while self.check(...) : ...` |
| **Grouping** | `( α \| β )` | Grouping sub-expressions or alternatives |
| **Alternative** | `α \| β` | `if ... elif ... else` branch selection |
| **Terminals** | `UPPERCASE` or `"literal"` | `self.consume(TokenType.X)` |

---

## 2. Program Structure & Statements

```ebnf
Program             = { Statement } EOF ;

Statement           = CompoundStatement
                    | SimpleStatement ;

CompoundStatement   = FunctionDef
                    | IfStatement
                    | WhileStatement
                    | ForStatement
                    | MatchStatement
                    | ClassDef
                    | SpecDef ;

SimpleStatement     = [ SmallStatement ] NEWLINE ;

SmallStatement      = VariableDeclOrAssign
                    | ReturnStatement
                    | BreakStatement
                    | ContinueStatement
                    | ImportStatement
                    | ExpressionStatement ;

Block               = ":" NEWLINE INDENT { Statement } DEDENT ;
```

---

## 3. Declarations

### 3.1 Function Definition
```ebnf
FunctionDef         = "fn" IDENTIFIER "(" [ ParameterList ] ")" [ "->" Type ] Block ;

ParameterList       = Parameter { "," Parameter } [ "," ] ;

Parameter           = IDENTIFIER [ ":" Type ] ;
```

### 3.2 Class and Spec Definition
```ebnf
ClassDef            = "class" IDENTIFIER [ "(" TypeList ")" ] ":" NEWLINE INDENT { ClassMember } DEDENT ;

ClassMember         = [ "+" | "-" ] ( FunctionDef | FieldDecl ) ;

FieldDecl           = IDENTIFIER ":" Type [ "=" Expression ] NEWLINE ;

SpecDef             = "spec" IDENTIFIER ":" NEWLINE INDENT { SpecMember } DEDENT ;

SpecMember          = "fn" IDENTIFIER "(" [ ParameterList ] ")" [ "->" Type ] NEWLINE
                    | IDENTIFIER ":" Type NEWLINE ;
```

---

## 4. Variables & Assignment

```ebnf
VariableDeclOrAssign = Target ( ":" Type "=" Expression | "=" Expression | CompoundAssignOp Expression ) ;

CompoundAssignOp     = "+=" | "-=" | "*=" | "/=" | "%=" ;

Target               = IDENTIFIER { "." IDENTIFIER | "[" Expression "]" } ;
```

---

## 5. Control Flow

### 5.1 If / Elif / Else
```ebnf
IfStatement         = "if" Expression Block { "elif" Expression Block } [ "else" Block ] ;
```

### 5.2 Loops (While & For)
```ebnf
WhileStatement      = "while" Expression Block ;

ForStatement        = "for" ForTarget "in" Expression Block ;

ForTarget           = IDENTIFIER | "(" TargetList ")" | "[" TargetList "]" ;

TargetList          = IDENTIFIER { "," IDENTIFIER } [ "," ] ;
```

### 5.3 Match / Case
```ebnf
MatchStatement      = "match" Expression ":" NEWLINE INDENT { CaseClause } DEDENT ;

CaseClause          = "case" Pattern [ "if" Expression ] ( Block | "=>" SimpleStatement ) ;

Pattern             = Literal
                    | IDENTIFIER
                    | "(" [ Pattern { "," Pattern } [ "," ] ] ")"
                    | "[" [ Pattern { "," Pattern } [ "," ] ] "]" ;
```

---

## 6. Simple Statements

```ebnf
ReturnStatement     = "return" [ Expression ] ;

BreakStatement      = "break" ;

ContinueStatement   = "continue" ;

ExpressionStatement = Expression ;

ImportStatement     = "import" DottedName [ "as" IDENTIFIER ]
                    | "from" DottedName "import" ImportSymbols ;

ImportSymbols       = ImportSymbol { "," ImportSymbol } [ "," ] ;

ImportSymbol        = IDENTIFIER [ "as" IDENTIFIER ] ;

DottedName          = IDENTIFIER { "." IDENTIFIER } ;
```

---

## 7. Expressions & Operator Precedence

In EBNF, operator precedence is expressed clearly without recursive tail-expansion non-terminals. Every level corresponds to a single method in the recursive-descent parser:

```ebnf
(* Level 1: Conditional / Ternary Expression *)
Expression          = LogicalOrExpr [ "if" LogicalOrExpr "else" Expression ] ;

(* Level 2: Logical OR *)
LogicalOrExpr       = LogicalAndExpr { "or" LogicalAndExpr } ;

(* Level 3: Logical AND *)
LogicalAndExpr      = LogicalNotExpr { "and" LogicalNotExpr } ;

(* Level 4: Logical NOT *)
LogicalNotExpr      = "not" LogicalNotExpr
                    | ComparisonExpr ;

(* Level 5: Comparisons *)
ComparisonExpr      = RangeExpr { ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) RangeExpr } ;

(* Level 6: Range Operator *)
RangeExpr           = AdditiveExpr [ ".." AdditiveExpr ] ;

(* Level 7: Addition and Subtraction *)
AdditiveExpr        = MultiplicativeExpr { ( "+" | "-" ) MultiplicativeExpr } ;

(* Level 8: Multiplication, Division, Floor Division, Modulo *)
MultiplicativeExpr  = UnaryExpr { ( "*" | "/" | "//" | "%" ) UnaryExpr } ;

(* Level 9: Unary Prefix *)
UnaryExpr           = ( "+" | "-" ) UnaryExpr
                    | PowerExpr ;

(* Level 10: Exponentiation (Right-Associative) *)
PowerExpr           = PostfixExpr [ "**" UnaryExpr ] ;

(* Level 11: Postfix Calls, Indexing, Slicing, Member Access *)
PostfixExpr         = PrimaryExpr { CallSuffix | IndexOrSliceSuffix | MemberAccessSuffix } ;

CallSuffix          = "(" [ ArgumentList ] ")" ;

ArgumentList        = Expression { "," Expression } [ "," ] ;

IndexOrSliceSuffix  = "[" ( Expression [ ":" [ Expression ] [ ":" [ Expression ] ] ]
                          | ":" [ Expression ] [ ":" [ Expression ] ] ) "]" ;

MemberAccessSuffix  = "." IDENTIFIER ;
```

---

## 8. Primary Expressions, Literals & Collections

```ebnf
PrimaryExpr         = Literal
                    | StringInterpolation
                    | ArrowFunction
                    | IDENTIFIER
                    | "(" [ Expression [ "," [ ExpressionList ] ] ] ")"
                    | "[" [ ExpressionList ] "]"
                    | "{" [ KeyValueList ] "}" ;

(* Arrow Function: fn(a: int, b: int): int => a + b *)
ArrowFunction       = "fn" "(" [ ParameterList ] ")" [ ":" Type ] "=>" Expression ;

Literal             = INTEGER | FLOAT | STRING | BOOL | NONE ;

(* Backtick String Interpolation *)
StringInterpolation = STRING { "{" Expression "}" STRING } ;

ExpressionList      = Expression { "," Expression } [ "," ] ;

KeyValueList        = KeyValuePair { "," KeyValuePair } [ "," ] ;

KeyValuePair        = Expression ":" Expression ;
```

---

## 9. Types

```ebnf
Type                = IDENTIFIER [ "[" TypeList "]" ] ;

TypeList            = Type { "," Type } [ "," ] ;
```

---

## 10. Direct Mapping: EBNF to Recursive Descent Code

Here is how each EBNF construct translates directly into Python methods inside `src/parser/parser.py`:

```python
# EBNF: AdditiveExpr = MultiplicativeExpr { ( "+" | "-" ) MultiplicativeExpr } ;
def parse_additive(self) -> ExprNode:
    expr = self.parse_multiplicative()
    while self.match(TokenType.PLUS, TokenType.MINUS):
        operator = self.previous()
        right = self.parse_multiplicative()
        expr = BinaryExpr(left=expr, op=operator, right=right)
    return expr

# EBNF: IfStatement = "if" Expression Block { "elif" Expression Block } [ "else" Block ] ;
def parse_if_statement(self) -> IfStmtNode:
    self.consume(TokenType.IF, "Expected 'if'")
    condition = self.parse_expression()
    then_branch = self.parse_block()
    elif_branches = []
    while self.match(TokenType.ELIF):
        elif_cond = self.parse_expression()
        elif_body = self.parse_block()
        elif_branches.append((elif_cond, elif_body))
    else_branch = self.parse_block() if self.match(TokenType.ELSE) else None
    return IfStmtNode(condition, then_branch, elif_branches, else_branch)
```
