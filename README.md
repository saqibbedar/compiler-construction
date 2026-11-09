# Introduction: Compiler Construction Course

The compiler construction is a BS seventh semester course taught at CS department, QAU, Islamabad, Pakistan. This course focuses on primarily building the compilers using various methodologies. And we student build compilers for our own programming languages. 

## Group Project

Students work in groups and our group is: 

- **Saqib Bedar**
- **Hamza Khan Tariq**
- **Humaira**

## Our Language

Each student has proposed a language that they will build through the semester and its the part of the assignment and so we are doing and pushing all changes in this repository to preserve our progress and also save our working copy. 

We have proposed a python like language, its almost similar to python but we have many things that will differ it in the final results but maybe we don't bring those changes in this repository as that is my personal project, however, current implementation is just about learning the compiler and implementation of its various components, i.e., lexer, parser, etc. 

> Note: Our actual implementations will be in C++ but however we are currently implementing our language in python just for simplicity.

# Folder Structure

This is important section, as I have dump many things in this repository. I will divide this whole repo into tow categories, one is language_implementation and other supporting_docs. The language_implementation contains language implementation files and supporting_docs contains books, slides and exam preparation stuff. So, if you want to see how language is build that we have been working on simply look directly into src directory and other supporting files for various connections to start application properly.

```txt
# supporting docs
├── assignments-and-notes       # assignments
└── course-material             # course material

# language implementation
├── examples                    # our language files
├── Justfile                    # quick just commands
├── pyproject.toml              # dependencies
├── README.md
├── scripts                     # quick scripts for automation
│   └── code_quality.py         # maintain code quality using ruff script
├── src                         # main language source code
│   ├── __init__.py
│   ├── lexer                   # lexer implementation
│   │   ├── errors.py
│   │   ├── __init__.py
│   │   ├── lexer.py
│   │   └── tokens.py
│   ├── parser                   # parser implementation (coming soon)
│   └── main.py                 # main file to run the application
└── uv.lock
```

# Get Started

To quickly get started, first clone this repository and follow alongside commands as the next steps:

```bash
# clone repo and open it in vscode
git clone https://github.com/saqibbedar/compiler-construction.git && cd compiler-construction && code .

# uv setup (make sure you have uv installed on your machine)
uv venv 
source .venv/bin/activate
uv sync

# run language files (language code is written inside examples dir and file is automatically read by main.py so run main.py and everything will execute dynamically)
uv run python src/main.py       # OR if you have just installed on your system run: just run main

# before you push the code on main branch make sure to run ruff tests
uv run python scripts/code_quality.py   # OR if you have just installed on your system run: just run cq
```

# LICENSE

No dedicated license up till now. You are allowed to download and contribute to this project but still we haven't fully added any guidelines so license remained unknown still.

# Course Metadata

- Group Members:
    - **Saqib Bedar**
    - **Hamza Khan Tariq**
    - **Humaira**

- Supervised by:
    - [**Dr. Syed Muhammad Naqi**](https://cs.qau.edu.pk/faculty/syed-muhammad-naqi)