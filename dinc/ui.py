"""Terminal output and prompts: colors, boxed menus, and input helpers."""

from getpass import getpass
import os
import shutil
import sys

# Windows only turns on ANSI escape codes for a console once something asks for
# it, and an empty os.system call is the cheapest way to ask.
if os.name == "nt":
    os.system("")

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

WIDTH = 64


def _paint(code, text):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def bold(text):
    return _paint("1", text)


def dim(text):
    return _paint("2", text)


def green(text):
    return _paint("32", text)


def yellow(text):
    return _paint("33", text)


def red(text):
    return _paint("31", text)


def cyan(text):
    return _paint("36", text)


def _visible_len(text):
    # Length without the escape codes, so colored text still lines up.
    length, in_escape = 0, False
    for char in text:
        if char == "\033":
            in_escape = True
        elif in_escape:
            in_escape = char != "m"
        else:
            length += 1
    return length


def _row(text=""):
    padding = WIDTH - 4 - _visible_len(text)
    return f"| {text}{' ' * max(padding, 0)} |"


def _rule(char="-"):
    return "+" + char * (WIDTH - 2) + "+"


def clear():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def box(title, sections):
    """Print a box with a centered title and sections of lines between rules."""
    print(_rule("="))
    print(_row(bold(title.center(WIDTH - 4))))
    for lines in sections:
        print(_rule())
        for line in lines:
            print(_row(line))
    print(_rule("="))


# Plain messages, one per line, prefixed so they're easy to scan.
def info(message):
    print(f"{cyan('::')} {message}")


def ok(message):
    print(f"{green('ok')} {message}")


def warn(message):
    print(f"{yellow('!!')} {message}")


def error(message):
    print(f"{red('xx')} {message}", file=sys.stderr)


def heading(message):
    print()
    print(bold(message))
    print(dim("-" * min(len(message), shutil.get_terminal_size().columns)))


def ask(prompt, default=None, required=True):
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{prompt}{suffix}: ").strip()
        if answer:
            return answer
        if default is not None:
            return default
        if not required:
            return ""
        warn("This one can't be blank.")


def ask_secret(prompt, required=True):
    # Hidden input, for keys and passwords. Nothing shows up as you type or paste.
    while True:
        answer = getpass(f"{prompt} (hidden): ").strip()
        if answer or not required:
            return answer
        warn("This one can't be blank.")


def confirm(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def pause():
    if sys.stdin.isatty():
        input(dim("\nPress Enter to go back to the menu..."))
