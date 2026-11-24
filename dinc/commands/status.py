"""What state the install and stack are in."""

import time

from .. import compose, migrations, paths, state, ui
from ..envfile import EnvFile


def summary():
    """A few short lines describing the install, for the menu header."""
    if not paths.ENV_FILE.exists():
        return [f"Install:  {ui.yellow('not installed')}"]

    project = EnvFile(paths.ENV_FILE).get("PROJECT_NAME", "?")
    lines = [f"Install:  {ui.green('installed')} (project {project})"]

    if not compose.available():
        lines.append(f"Stack:    {ui.yellow('docker not found')}")
    else:
        try:
            states = compose.services()
            running = sum(1 for s in states.values() if s == "running")
            color = ui.green if running == len(states) else ui.yellow if running else ui.dim
            lines.append(f"Stack:    {color(f'{running}/{len(states)} services running')}")
        except compose.ComposeError:
            lines.append(f"Stack:    {ui.red('docker compose failed')}")

    waiting = migrations.pending()
    if waiting or not state.exists():
        lines.append(f"Updates:  {ui.yellow('migrations waiting, run Update')}")
    else:
        lines.append(f"Updates:  {ui.green('all migrations applied')}")
    return lines


def _when(timestamp):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(timestamp)))


def run(args):
    ui.heading("Install")
    if not paths.ENV_FILE.exists():
        print("Not installed. Run Install to set DINC up.")
        return 0
    env = EnvFile(paths.ENV_FILE)
    print(f"Project name:  {env.get('PROJECT_NAME', '?')}")
    for key, label in (("installed_at", "Installed"), ("adopted_at", "First tracked"),
                       ("updated_at", "Last update")):
        value = state.get_meta(key)
        if value:
            print(f"{label + ':':<15}{_when(value)}")

    ui.heading("Services")
    if not compose.available():
        print("Docker isn't installed (or isn't on your PATH).")
    else:
        for name, service_state in compose.services().items():
            shown = service_state or "not created"
            color = ui.green if service_state == "running" else ui.yellow
            print(f"{name:<15}{color(shown)}")

    ui.heading("Migrations")
    done = {(row[0], row[1]): row[3] for row in state.history()}
    start = migrations.baseline()
    if start:
        print(ui.dim(f"Installed after migration {start:04d}, so the ones up to it were never needed."))
    for migration in migrations.discover():
        if migration.id <= start:
            print(ui.dim(f"{migration.id:04d} {'':<10}not needed  {migration.description}"))
            continue
        for phase in migration.phases:
            applied_at = done.get((migration.id, phase))
            mark = ui.green(f"ran {_when(applied_at)}") if applied_at else ui.yellow("waiting")
            print(f"{migration.id:04d} {phase:<10}{mark}  {migration.description}")
    return 0
