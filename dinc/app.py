"""The entry point: a numbered menu when run bare, or one command when given a
subcommand (`python DINC.py update`)."""

import argparse
import sys

from . import compose, ui
from .commands import COMMANDS

BANNER = "DINC  -  your self hosted ChatGPT"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="DINC.py",
        description="Install, update and manage your DINC stack. Run with no arguments for a menu.",
    )
    sub = parser.add_subparsers(dest="command")
    for command in COMMANDS:
        cmd_parser = sub.add_parser(command.name, help=command.help)
        if command.name == "update":
            cmd_parser.add_argument("--no-pull", action="store_true",
                                    help="skip `git pull` and use the code that's here")
        if command.name == "logs":
            cmd_parser.add_argument("service", nargs="?", help="one service (default: all)")
    return parser


def _run(command, args):
    try:
        return command.run(args) or 0
    except compose.ComposeError as e:
        ui.error(str(e))
    except KeyboardInterrupt:
        print()
        ui.warn("Cancelled.")
    except Exception as e:  # Keep the menu alive, but say what broke.
        ui.error(f"{type(e).__name__}: {e}")
    return 1


def _render_menu():
    from .commands.status import summary

    groups = {}
    for number, command in enumerate(COMMANDS, start=1):
        groups.setdefault(command.group, []).append(f"  {ui.cyan(str(number) + ')')} {command.label}")
    sections = [summary()]
    for group, lines in groups.items():
        sections.append([ui.bold(group)] + lines)
    sections.append([f"  {ui.cyan('q)')} Quit"])
    ui.clear()
    ui.box(BANNER, sections)


def menu():
    blank = argparse.Namespace()
    while True:
        _render_menu()
        choice = input("\nPick an option: ").strip().lower()
        if choice in ("q", "quit", "exit"):
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(COMMANDS):
            print()
            _run(COMMANDS[int(choice) - 1], blank)
            ui.pause()


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command is None:
        if not sys.stdin.isatty():
            build_parser().print_help()
            return 1
        try:
            return menu()
        except (KeyboardInterrupt, EOFError):
            print()
            return 0
    command = next(c for c in COMMANDS if c.name == args.command)
    return _run(command, args)
