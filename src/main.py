from pathlib import Path

from lexer import Lexer
from parser import Parser, dump_ast

# access main.cmm file
cmm_file = (Path(__file__).parent.parent / "examples" / "main.cmm").resolve()

print(f"\n--- Running File {cmm_file} ---\n")

# if file not available then use default method
if not cmm_file.exists():
    print("--- Error: unable to read main.cmm file ---")
    print("--- Using default source method for testing ---")

    source = "total = 42"
    tokens = Lexer(source=source).scan_tokens()

    for token in tokens:
        print(token)

    parser = Parser(tokens=tokens)
    ast = parser.parse()
    print("\n--- Parsed AST ---")
    print(dump_ast(ast))
    exit(0)


# read main.cmm file using context manager
with open(cmm_file, "r") as file:
    source = file.read()

# Pass 1: Lexical Analysis
lexer: Lexer = Lexer(source=source)
tokens: list = lexer.scan_tokens()

for token in tokens:
    print(token)

if lexer.errors:
    print(f"\n--- Lexical Errors ({len(lexer.errors)}) ---")
    for error in lexer.errors:
        print(error)
else:
    print(f"\n--- [Pass 1] Lexer: Successfully scanned {len(tokens)} tokens with 0 errors! ---")

# Pass 2: Syntax Analysis (Recursive-Descent Parser)
parser: Parser = Parser(tokens=tokens)
ast = parser.parse()

if parser.errors:
    print(f"\n--- Syntax / Parse Errors ({len(parser.errors)}) ---")
    for error in parser.errors:
        print(error)
else:
    print(f"--- [Pass 2] Parser: Successfully parsed {len(ast.statements)} top-level statements with 0 errors! ---")
    print("\n--- Abstract Syntax Tree (AST) ---")
    print(dump_ast(ast))
