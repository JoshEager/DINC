"""Everything DINC.py can do. Each entry is both a menu item and a subcommand
(`python DINC.py <name>`), so adding one here adds it to both."""

from dataclasses import dataclass
from typing import Callable

from . import agents, install, services, settings, status, update


@dataclass
class Command:
    name: str
    label: str
    help: str
    run: Callable
    group: str


COMMANDS = [
    Command("install", "Install", "first time setup", install.run, "Setup"),
    Command("update", "Update", "pull new code and images, run migrations", update.run, "Setup"),
    Command("status", "Status", "show services and migrations", status.run, "Setup"),
    Command("start", "Start", "start the stack", services.start, "Stack"),
    Command("stop", "Stop", "stop the stack", services.stop, "Stack"),
    Command("restart", "Restart", "restart the stack", services.restart, "Stack"),
    Command("logs", "Logs", "follow a service's logs", services.logs, "Stack"),
    Command("openrouter-key", "Change OpenRouter key", "use a new OpenRouter key everywhere",
            settings.openrouter_key, "Settings"),
    Command("agents", "ACP agents", "register extra ACP agents with Open Terminal",
            agents.run, "Settings"),
]
