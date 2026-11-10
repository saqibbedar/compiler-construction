# C-- Backus-Naur Form (BNF) Specification

## 1. Overview & Conventions

This document specifies the formal **Backus-Naur Form (BNF)** grammar for the **C--** programming language, derived from the verified Context-Free Grammar.

### BNF Notation Rules:
- **Non-terminals**: Enclosed in angle brackets, e.g. `<program>`, `<statement>`, `<expression>`.
- **Production Operator**: `::=`, read as "is defined as" or "produces".
- **Alternatives**: Separated by vertical bars `|`.
- **Terminals**: Written in `UPPERCASE` matching the lexer tokens (e.g. `IDENTIFIER`, `INTEGER`, `IF`, `COLON`, `NEWLINE`, `INDENT`, `DEDENT`) or literal symbols in quotes (e.g. `":="`, `"+"`, `"->"`).
- **Empty String (Epsilon)**: Denoted by `<empty>`.
- **Pure BNF**: Repetition and optional constructs are expressed purely via recursion and `<empty>` without regex shorthands (for regex extensions like `[...]` and `{...}`, see [EBNF.md](EBNF.md)).

---

## 2. Program Structure & Statements

```bnf
<program> ::= <statement_list> EOF

<statement_list> ::= <statement> <statement_list>
                   | <empty>

<statement> ::= <compound_statement>
              | <simple_statement>

<compound_statement> ::= <function_def>
                       | <if_statement>
                       | <while_statement>
                       | <for_statement>
                       | <match_statement>
                       | <class_def>
                       | <spec_def>

<simple_statement> ::= <small_statement> NEWLINE
                     | NEWLINE

<small_statement> ::= <variable_decl_or_assign>
                    | <return_statement>
                    | <break_statement>
                    | <continue_statement>
                    | <import_statement>
                    | <expression_statement>

<block> ::= COLON NEWLINE INDENT <statement_list> DEDENT
```

---

## 3. Declarations

### 3.1 Function Definition
```bnf
<function_def> ::= FN IDENTIFIER LPAREN <parameter_list_opt> RPAREN <return_type_opt> <block>

<parameter_list_opt> ::= <parameter_list>
                       | <empty>

<parameter_list> ::= <parameter> <parameter_list_tail>

<parameter_list_tail> ::= COMMA <parameter> <parameter_list_tail>
                        | COMMA
                        | <empty>

<parameter> ::= IDENTIFIER <type_annotation_opt>

<type_annotation_opt> ::= COLON <type>
                        | <empty>

<return_type_opt> ::= ARROW <type>
                    | <empty>
```

### 3.2 Class and Spec Definition
```bnf
<class_def> ::= CLASS IDENTIFIER <class_heritage_opt> COLON NEWLINE INDENT <class_body> DEDENT

<class_heritage_opt> ::= LPAREN <type_list> RPAREN
                       | <empty>

<class_body> ::= <class_member> <class_body>
               | <empty>

<class_member> ::= <member_visibility_opt> <member_definition>

<member_visibility_opt> ::= PLUS
                          | MINUS
                          | <empty>

<member_definition> ::= <function_def>
                      | <field_decl>

<field_decl> ::= IDENTIFIER COLON <type> <field_init_opt> NEWLINE

<field_init_opt> ::= ASSIGN <expression>
                   | <empty>

<spec_def> ::= SPEC IDENTIFIER COLON NEWLINE INDENT <spec_body> DEDENT

<spec_body> ::= <spec_member> <spec_body>
              | <empty>

<spec_member> ::= FN IDENTIFIER LPAREN <parameter_list_opt> RPAREN <return_type_opt> NEWLINE
                | IDENTIFIER COLON <type> NEWLINE
```

---

## 4. Variables & Assignment

```bnf
<variable_decl_or_assign> ::= <target> <assign_rest>

<assign_rest> ::= COLON <type> ASSIGN <expression>
                | ASSIGN <expression>
                | <compound_assign_op> <expression>

<compound_assign_op> ::= PLUS_EQ
                       | MINUS_EQ
                       | MUL_EQ
                       | DIV_EQ
                       | MOD_EQ

<target> ::= IDENTIFIER <target_suffix_list>

<target_suffix_list> ::= <target_suffix> <target_suffix_list>
                       | <empty>

<target_suffix> ::= DOT IDENTIFIER
                  | LBRACKET <expression> RBRACKET
```

---

## 5. Control Flow

### 5.1 If / Elif / Else
```bnf
<if_statement> ::= IF <expression> <block> <elif_list> <else_opt>

<elif_list> ::= <elif_clause> <elif_list>
              | <empty>

<elif_clause> ::= ELIF <expression> <block>

<else_opt> ::= ELSE <block>
             | <empty>
```

### 5.2 Loops (While & For)
```bnf
<while_statement> ::= WHILE <expression> <block>

<for_statement> ::= FOR <for_target> IN <expression> <block>

<for_target> ::= IDENTIFIER
               | LPAREN <target_list> RPAREN
               | LBRACKET <target_list> RBRACKET

<target_list> ::= IDENTIFIER <target_list_tail>

<target_list_tail> ::= COMMA IDENTIFIER <target_list_tail>
                     | COMMA
                     | <empty>
```

### 5.3 Match / Case Pattern Matching
```bnf
<match_statement> ::= MATCH <expression> COLON NEWLINE INDENT <case_list> DEDENT

<case_list> ::= <case_clause> <case_list>
              | <empty>

<case_clause> ::= CASE <pattern> <case_guard_opt> <case_body>

<case_guard_opt> ::= IF <expression>
                   | <empty>

<case_body> ::= <block>
              | FAT_ARROW <simple_statement>

<pattern> ::= <literal>
            | IDENTIFIER
            | <pattern_tuple>
            | <pattern_list>

<pattern_tuple> ::= LPAREN <pattern_elements_opt> RPAREN

<pattern_list> ::= LBRACKET <pattern_elements_opt> RBRACKET

<pattern_elements_opt> ::= <pattern> <pattern_elements_tail>
                         | <empty>

<pattern_elements_tail> ::= COMMA <pattern> <pattern_elements_tail>
                          | COMMA
                          | <empty>
```

---

## 6. Simple Statements

```bnf
<return_statement> ::= RETURN <expression_opt>

<expression_opt> ::= <expression>
                   | <empty>

<break_statement> ::= BREAK

<continue_statement> ::= CONTINUE

<expression_statement> ::= <expression>

<import_statement> ::= IMPORT <dotted_name> <import_alias_opt>
                     | FROM <dotted_name> IMPORT <import_symbols>

<import_alias_opt> ::= AS IDENTIFIER
                     | <empty>

<import_symbols> ::= <import_symbol> <import_symbols_tail>

<import_symbols_tail> ::= COMMA <import_symbol> <import_symbols_tail>
                        | COMMA
                        | <empty>

<import_symbol> ::= IDENTIFIER <import_alias_opt>

<dotted_name> ::= IDENTIFIER <dotted_name_tail>

<dotted_name_tail> ::= DOT IDENTIFIER <dotted_name_tail>
                     | <empty>
```

---

## 7. Expressions (Unambiguous & Non-Left-Recursive)

```bnf
<expression> ::= <conditional_expr>

<conditional_expr> ::= <logical_or_expr> <conditional_tail>

<conditional_tail> ::= IF <logical_or_expr> ELSE <conditional_expr>
                     | <empty>

<logical_or_expr> ::= <logical_and_expr> <logical_or_tail>

<logical_or_tail> ::= OR <logical_and_expr> <logical_or_tail>
                    | <empty>

<logical_and_expr> ::= <logical_not_expr> <logical_and_tail>

<logical_and_tail> ::= AND <logical_not_expr> <logical_and_tail>
                     | <empty>

<logical_not_expr> ::= NOT <logical_not_expr>
                     | <comparison_expr>

<comparison_expr> ::= <range_expr> <comparison_tail>

<comparison_tail> ::= <comparison_op> <range_expr> <comparison_tail>
                    | <empty>

<comparison_op> ::= EQ
                  | NOT_EQ
                  | LT
                  | LT_EQ
                  | GT
                  | GT_EQ

<range_expr> ::= <additive_expr> <range_tail>

<range_tail> ::= RANGE <additive_expr>
               | <empty>

<additive_expr> ::= <multiplicative_expr> <additive_tail>

<additive_tail> ::= <additive_op> <multiplicative_expr> <additive_tail>
                  | <empty>

<additive_op> ::= PLUS
                | MINUS

<multiplicative_expr> ::= <unary_expr> <multiplicative_tail>

<multiplicative_tail> ::= <multiplicative_op> <unary_expr> <multiplicative_tail>
                        | <empty>

<multiplicative_op> ::= MUL
                      | DIV
                      | FLOOR_DIV
                      | MOD

<unary_expr> ::= PLUS <unary_expr>
               | MINUS <unary_expr>
               | <power_expr>

<power_expr> ::= <postfix_expr> <power_tail>

<power_tail> ::= POW <unary_expr>
               | <empty>

<postfix_expr> ::= <primary_expr> <postfix_tail>

<postfix_tail> ::= <postfix_op> <postfix_tail>
                 | <empty>

<postfix_op> ::= <call_suffix>
               | <index_or_slice_suffix>
               | <member_access_suffix>

<call_suffix> ::= LPAREN <argument_list_opt> RPAREN

<argument_list_opt> ::= <argument_list>
                      | <empty>

<argument_list> ::= <argument> <argument_list_tail>

<argument_list_tail> ::= COMMA <argument> <argument_list_tail>
                       | COMMA
                       | <empty>

<argument> ::= <expression>

<index_or_slice_suffix> ::= LBRACKET <slice_content> RBRACKET

<slice_content> ::= <expression> <slice_content_tail>
                  | COLON <slice_end_opt> <slice_step_opt>

<slice_content_tail> ::= COLON <slice_end_opt> <slice_step_opt>
                       | <empty>

<slice_end_opt> ::= <expression>
                  | <empty>

<slice_step_opt> ::= COLON <expression_opt>
                   | <empty>

<member_access_suffix> ::= DOT IDENTIFIER
```

---

## 8. Primary Expressions, Literals & Arrow Functions

```bnf
<primary_expr> ::= <literal>
                 | <string_interpolation>
                 | <arrow_function>
                 | IDENTIFIER
                 | <grouped_or_tuple_expr>
                 | <list_literal>
                 | <dict_literal>

<arrow_function> ::= FN LPAREN <parameter_list_opt> RPAREN <arrow_return_type_opt> FAT_ARROW <expression>

<arrow_return_type_opt> ::= COLON <type>
                          | <empty>

<literal> ::= INTEGER
            | FLOAT
            | STRING
            | BOOL
            | NONE

<string_interpolation> ::= STRING <string_interpolation_tail>

<string_interpolation_tail> ::= LBRACE <expression> RBRACE STRING <string_interpolation_tail>
                              | <empty>

<grouped_or_tuple_expr> ::= LPAREN <grouped_or_tuple_body> RPAREN

<grouped_or_tuple_body> ::= <expression> <grouped_or_tuple_tail>
                          | <empty>

<grouped_or_tuple_tail> ::= COMMA <expression_list_opt>
                          | <empty>

<expression_list_opt> ::= <expression_list>
                        | <empty>

<expression_list> ::= <expression> <expression_list_tail>

<expression_list_tail> ::= COMMA <expression> <expression_list_tail>
                         | COMMA
                         | <empty>

<list_literal> ::= LBRACKET <expression_list_opt> RBRACKET

<dict_literal> ::= LBRACE <key_value_list_opt> RBRACE

<key_value_list_opt> ::= <key_value_list>
                       | <empty>

<key_value_list> ::= <key_value_pair> <key_value_list_tail>

<key_value_list_tail> ::= COMMA <key_value_pair> <key_value_list_tail>
                        | COMMA
                        | <empty>

<key_value_pair> ::= <expression> COLON <expression>
```

---

## 9. Type Expressions

```bnf
<type> ::= IDENTIFIER <type_arguments_opt>

<type_arguments_opt> ::= LBRACKET <type_list> RBRACKET
                       | <empty>

<type_list> ::= <type> <type_list_tail>

<type_list_tail> ::= COMMA <type> <type_list_tail>
                   | COMMA
                   | <empty>
```
