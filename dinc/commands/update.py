"""Bring an install up to date: new code, migrations, and new images."""

import subprocess
import sys
import time

from .. import compose, migrations, openwebui, paths, state, ui


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=paths.PROJECT, text=True, capture_output=True
    )


def pull_code():
    """git pull. Returns True if new code came in."""
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        ui.info("Not a git checkout, so skipping the code update.")
        return False
    before = _git("rev-parse", "HEAD").stdout.strip()
    result = _git("pull", "--ff-only")
    if result.returncode != 0:
        ui.warn("Couldn't pull the latest code, so carrying on with what's here:")
        print(result.stderr.strip())
        return False
    after = _git("rev-parse", "HEAD").stdout.strip()
    if before == after:
        ui.ok("Code is already up to date.")
        return False
    ui.ok(f"Updated code from {before[:7]} to {after[:7]}.")
    return True


def run(args):
    if not paths.ENV_FILE.exists():
        ui.warn("DINC isn't installed here yet. Run Install first.")
        return 1

    ui.heading("Updating DINC")

    if not getattr(args, "no_pull", False) and pull_code():
        # The new code may bring new migrations (or a new version of this very
        # command), so hand over to it instead of carrying on with the old one.
        ui.info("Restarting DINC.py on the new code...")
        return subprocess.call(
            [sys.executable, str(paths.PROJECT / "DINC.py"), "update", "--no-pull"]
        )

    if not state.exists():
        # Installed before DINC.py kept a record. Every migration is written to
        # be safe to repeat, so run them all once.
        ui.info("No record of past updates on this install, so running every migration once.")
        state.set_meta("adopted_at", int(time.time()))

    paths.ensure_data_dirs()
    count = migrations.run("prepare")

    ui.info("Pulling the latest images...")
    compose.run("pull")
    ui.info("Starting the stack...")
    compose.run("up", "-d", "--remove-orphans")

    if migrations.pending("openwebui"):
        ui.info("Waiting for Open WebUI to finish starting...")
        compose.wait_for_openwebui()
        ui.ok(f"Backed up Open WebUI's database to {openwebui.backup()}.")
        count += migrations.run("openwebui")

    state.set_meta("updated_at", int(time.time()))
    ui.ok(f"DINC is up to date ({count} migration step{'s' if count != 1 else ''} ran).")
    return 0
