"""Starting, stopping, and watching the stack."""

import sys

from .. import compose, ui


def start(args):
    compose.run("up", "-d")
    ui.ok("The stack is up.")
    return 0


def stop(args):
    compose.run("stop")
    ui.ok("The stack is stopped. Nothing was deleted.")
    return 0


def restart(args):
    compose.run("restart")
    ui.ok("The stack restarted.")
    return 0


def logs(args):
    service = getattr(args, "service", None)
    if service is None and sys.stdin.isatty():
        names = list(compose.services())
        print("Services: " + ", ".join(names))
        service = ui.ask("Which one (blank for all)", required=False) or None
    ui.info("Following logs. Press Ctrl+C to stop.")
    try:
        compose.run("logs", "--follow", "--tail", "100", *([service] if service else []), check=False)
    except KeyboardInterrupt:
        print()
    return 0
