"""Registering extra ACP agents with Open Terminal.

Open Terminal reads OPEN_TERMINAL_ACP_AGENTS, a JSON object of
{"<id>": {"name": ..., "command": ...}}, when it starts. docker-compose.yml
fills it from ACP_AGENTS in .env, so this command only edits .env and then
recreates the open-terminal container so it picks the change up.
"""

import json
import re
import shlex

from .. import compose, paths, ui
from ..envfile import EnvFile

ENV_KEY = "ACP_AGENTS"
SERVICE = "open-terminal"

# Open Terminal skips any id that doesn't match this.
_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")

# Where Open Terminal looks for agent commands, on top of the container's PATH.
_FIND_COMMAND = (
    'PATH="$HOME/.local/bin:$HOME/.cursor/bin:$HOME/.opencode/bin:$PATH" '
    "command -v -- {}"
)


def _load(env):
    raw = env.get(ENV_KEY) or ""
    if not raw.strip():
        return {}
    try:
        agents = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{ENV_KEY} in .env isn't valid JSON. Fix or remove it by hand first.")
    if not isinstance(agents, dict):
        raise ValueError(f"{ENV_KEY} in .env should be a JSON object. Fix or remove it by hand first.")
    return agents


def _save(env, agents):
    if agents:
        env.set(ENV_KEY, json.dumps(agents, separators=(",", ":")))
    else:
        env.remove(ENV_KEY)
    env.save()


def _show(agents):
    if not agents:
        ui.info("No extra ACP agents registered yet.")
        return
    print(ui.bold("Registered agents") + ui.dim("  (shown in Open WebUI as acp-<id>/<model>)"))
    for number, (agent_id, spec) in enumerate(agents.items(), start=1):
        name = spec.get("name") or agent_id
        print(f"  {ui.cyan(str(number) + ')')} {name} {ui.dim('(' + agent_id + ')')}")
        print(f"     {ui.dim(spec.get('command', ''))}")


def _ask_id(agents):
    while True:
        agent_id = ui.ask("Short id (lowercase letters, numbers, - or _)").lower()
        if not _ID.match(agent_id):
            ui.warn("Use 1 to 48 lowercase letters, numbers, - or _, starting with a letter or number.")
        elif agent_id in agents:
            ui.warn(f"There's already an agent called {agent_id}.")
        else:
            return agent_id


def _ask_command():
    while True:
        command = ui.ask("Command that starts it in ACP mode")
        try:
            parts = shlex.split(command)
        except ValueError as e:
            ui.warn(f"Couldn't read that command ({e}). Check the quotes.")
            continue
        if "'" in command:
            ui.warn("Use double quotes (\") instead of single quotes in the command.")
        elif parts:
            return command, parts[0]


def _check_installed(binary):
    """Warn if Open Terminal can't find binary. Only checks when it's running."""
    if not compose.is_running(SERVICE):
        return
    found = compose.run(
        "exec", "-T", SERVICE, "sh", "-c", _FIND_COMMAND.format(shlex.quote(binary)),
        capture=True, check=False,
    )
    if not (found or "").strip():
        ui.warn(f"Open Terminal can't find `{binary}` right now. Install it in the terminal")
        ui.warn("pane before you use the agent, or give the command's full path.")


def _add(env, agents):
    ui.heading("Register an ACP agent")
    print("Any agent that speaks ACP over stdio works. Check its docs for the command")
    print("that starts it in ACP mode. For example:")
    print(ui.dim("  Another Hermes profile:   hermes --profile work acp"))
    print(ui.dim("  Kiro:                     kiro-cli acp"))
    print()
    agent_id = _ask_id(agents)
    name = ui.ask("Name to show in Open WebUI", default=agent_id)
    if "'" in name:
        ui.warn("Names can't contain a single quote ('), so it was left out.")
        name = name.replace("'", "")
    command, binary = _ask_command()
    _check_installed(binary)
    agents[agent_id] = {"name": name, "command": command}
    _save(env, agents)
    ui.ok(f"Registered {name}. It will show up as acp-{agent_id}/<model>.")
    return True


def _remove(env, agents):
    if not agents:
        ui.info("There's nothing to remove.")
        return False
    ids = list(agents)
    choice = ui.ask("Number to remove (blank to cancel)", required=False)
    if not choice:
        return False
    if not choice.isdigit() or not 1 <= int(choice) <= len(ids):
        ui.warn("That isn't one of the numbers above.")
        return False
    agent_id = ids[int(choice) - 1]
    name = agents[agent_id].get("name") or agent_id
    if not ui.confirm(f"Remove {name}?", default=False):
        return False
    del agents[agent_id]
    _save(env, agents)
    ui.ok(f"Removed {name}. Its chats and the agent itself are untouched.")
    return True


def _apply():
    """Recreate open-terminal so it reads the new list."""
    if not compose.is_running(SERVICE):
        ui.info("Open Terminal isn't running. The change applies the next time it starts.")
        return
    if not ui.confirm("Restart Open Terminal now to apply it? Agent replies in progress will stop."):
        ui.info("Saved. It applies the next time Open Terminal restarts (`docker compose up -d open-terminal`).")
        return
    compose.run("up", "-d", SERVICE)
    ui.ok("Open Terminal restarted with the new agent list.")


def run(args):
    if not paths.ENV_FILE.exists():
        ui.warn("DINC isn't installed here yet. Run Install first.")
        return 1

    env = EnvFile(paths.ENV_FILE)
    try:
        agents = _load(env)
    except ValueError as e:
        ui.error(str(e))
        return 1

    ui.heading("ACP agents")
    print("Built-in agents (Claude Code, Codex, OpenCode, Hermes and so on) show up on")
    print("their own. Register an agent here when it isn't built in, or when you want a")
    print("second copy with a different setup, like another Hermes profile.\n")

    changed = False
    while True:
        _show(agents)
        print()
        choice = ui.ask("a) add   r) remove   Enter) done", required=False).lower()
        if not choice:
            break
        if choice in ("a", "add"):
            changed |= _add(env, agents)
        elif choice in ("r", "remove"):
            changed |= _remove(env, agents)
        print()

    if changed:
        _apply()
    return 0
