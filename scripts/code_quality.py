# code_quality: an automatic script to run ruff tests
# run file:
#       - using just: just cq

"""
These are the cmds will be executed directly on all modified or untracked files automatically.

uvx ruff check .
uvx ruff format .
uvx ruff check --fix .

and logs will be saved in .logs dir (if not already existing, a .logs will be created automatically)
"""

import locale
import subprocess  # for cmds to run in terminal
from datetime import datetime  # for logs time
from pathlib import Path  # for paths resolution

# importing GitPython from global dependency env "kernel" directory
# GitPython is installed at kernel dir and current selected env is kernel/.venv
# if you are using vscode then from root(*this repo) cd to kernel directory and run uv sync to install required dependencies, and then select the evn for python, in vscode you can do that via a bottom-bar list (look for Python X.X.X version) click on it and change your env with kernel/.venv/bin/python
import git  # for untracked and modified (unstaged) files
from yachalk import chalk  # improve terminal output


# create logs directory
def make_logs_dir(root_dir: Path | None = None):

    print(f"\n{chalk.bold.cyan('--- Attempting .logs directory creation ---')}\n")

    if root_dir is None:
        print(chalk.bold.red(f"- Invalid Path {root_dir}\n"))

    else:
        logs_dir: Path = (root_dir / ".logs").resolve()

        if logs_dir.exists():
            print(f"- .logs directory already exist at {chalk.yellow(str(logs_dir))}\n")

        else:
            # exist_ok: prevents errors if they already exist
            logs_dir.mkdir(exist_ok=True)
            print(chalk.green(f".logs directory was successfully created at {logs_dir}\n"))


# get the all untracked and modified (unstaged) files
def get_git_status(repo_path: Path = Path(".")) -> list[str | None] | None:
    try:
        # git repository object
        repo = git.Repo(repo_path)

        # 1. get untracked files
        untracked_files = repo.untracked_files

        # 2. get modified files (unstaged)
        modified_files = [item.a_path for item in repo.index.diff(None) if item.change_type == "M"]

        return [*untracked_files, *modified_files]

    except git.InvalidGitRepositoryError:
        print(chalk.bold.red(f"Error: {repo_path} is not a valid Git repository"))

    except git.NoSuchPathError:
        print(chalk.bold.red(f"Error: The path {repo_path} does not exist"))


# prepare the ROOT (path)
ROOT: Path = Path(__file__).parent.parent

# create .logs dir
make_logs_dir(ROOT)

# untracked and unstaged (modified) files
files: list[str | None] | None = get_git_status(ROOT)

# display files
print(f"{chalk.gray('-' * 50)}\n")
print(f"{chalk.bold.blue('--- Untracked And Modified (unstaged) file list ---')}\n")
print(chalk.yellow(str(files)), "\n")


# Ruff automatic tests
print(f"{chalk.gray('-' * 50)}\n")
print(chalk.bold.magenta("--- Running Ruff Tests ---"))

# shell=True: perform cmd exactly as we type in terminal
# text=True returns raw python string
# capture_output: capture output in variable

if files is not None:
    # filter only python files
    python_files: list[str] = [f for f in (files or []) if f and (f.endswith(".py") or f.endswith(".ipynb"))]

    if not python_files:
        print(chalk.yellow("No modified or untracked Python files found. Skipping Ruff."))
        exit(0)

# run ruff commands
ruff_check = subprocess.run(["uvx", "ruff", "check", *python_files], text=True, capture_output=True)
ruff_format = subprocess.run(["uvx", "ruff", "format", *python_files], text=True, capture_output=True)
ruff_check_fix = subprocess.run(["uvx", "ruff", "check", "--fix", *python_files], text=True, capture_output=True)


# prepare pretty output
def pretty_log_output() -> str:
    # Set to user's default system locale
    locale.setlocale(locale.LC_ALL, "")

    # prepare date & time
    now = datetime.now()

    time = now.strftime("%H:%M:%S")
    date = now.strftime("%Y-%m-%d")

    output = f"---------- Ruff Test Logs ----------\n\n- time: {time}\n- date: {date}\n\n"
    output += f"--- cmd: uvx ruff check ---\n[\n  {ruff_check.stdout + ruff_check.stderr}]\n\n"
    output += f"--- cmd: uvx ruff format ---\n[\n  {ruff_format.stdout + ruff_format.stderr}]\n\n"
    output += f"--- cmd: uvx ruff check --fix ---\n[\n  {ruff_check_fix.stdout + ruff_check_fix.stderr}]\n\n"

    return output


# save logs
with open(f"{(ROOT / '.logs' / 'ruff.txt')}", mode="w") as file:
    output: str = pretty_log_output()
    file.write(output)

print(f"{chalk.bold.green('--- All tests are done ----')}\n")
print(f"- View generated logs at {chalk.bold.cyan(str((ROOT / '.logs' / 'ruff.txt').resolve()))}")
