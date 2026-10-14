# To run this Justfile, you need to install Just
# Justfile for automatic scripts

# cq (code quality): run code quality checks on kernel directory
cq:
    uv run python scripts/code_quality.py