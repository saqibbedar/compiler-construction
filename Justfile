# To run this Justfile, you need to install Just
# Justfile for automatic scripts

# cq (code quality): run code quality checks on kernel directory
cq:
    uv run python scripts/code_quality.py

# run main.cmm through main.py file
run main:
    uv run python src/main.py