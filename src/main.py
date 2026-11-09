from pathlib import Path

from lexer import Lexer

# access main.cmm file
cmm_file = (Path(__file__).parent.parent / "examples" / "main.cmm").resolve()

# if file not available then use default method
if not cmm_file.exists():
    print("--- Error: unable to read main.cmm file ---")
    print("--- Using default source method for testing ---")

    source = "total = 42"
    tokens = Lexer(source=source).scan_tokens()  # returns tokens list

    for token in tokens:
        print(token)

    # End file
    exit(0)


# read main.cmm file using context manager
with open(cmm_file, "r") as file:
    source = file.read()

# check main.cmm file's data type
# print(type(source))     # <class 'str'>

lexer: Lexer = Lexer(source=source)
tokens: list = lexer.scan_tokens()  # list of tokens

# print tokens
for token in tokens:
    print(token)

# handle error (print errors separately after tokenization is successfully printed)
# this is just for error logs
if lexer.errors:
    print(f"\n--- Lexical Errors ({len(lexer.errors)}) ---")
    for error in lexer.errors:
        print(error)
else:
    print(f"\n--- Successfully scanned {len(tokens)} tokens with 0 errors! ---")
