"""Thin wrappers around `docker compose`, always run from the project folder so
it picks up docker-compose.yml and .env."""

import json
import shutil
import subprocess
import time

from . import paths


class ComposeError(RuntimeError):
    pass


def available():
    return shutil.which("docker") is not None


def run(*args, capture=False, check=True, input=None):
    """Run `docker compose <args>`. With capture, returns stdout as text."""
    command = ["docker", "compose", *args]
    result = subprocess.run(
        command,
        cwd=paths.PROJECT,
        input=input,
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or "").strip() if capture else ""
        raise ComposeError(f"`{' '.join(command)}` failed" + (f":\n{detail}" if detail else ""))
    return result.stdout if capture else result.returncode


def services():
    """Every service in the compose file mapped to its state ("running",
    "exited", ...), or None if it has no container."""
    names = run("config", "--services", capture=True).split()
    states = {name: None for name in names}
    output = run("ps", "--all", "--format", "json", capture=True, check=False) or ""
    # Newer compose prints one JSON object per line, older prints one array.
    output = output.strip()
    entries = json.loads(output) if output.startswith("[") else [
        json.loads(line) for line in output.splitlines() if line.strip()
    ]
    for entry in entries:
        states[entry.get("Service")] = entry.get("State")
    return states


def is_running(service):
    return services().get(service) == "running"


def exec_python(service, script, *args):
    """Run a Python script inside a running service's container and return its
    stdout. The script is sent over stdin, so nothing is copied into the
    container."""
    return run("exec", "-T", service, "python", "-", *args, capture=True, input=script)


_HEALTH_CHECK = """
import sys, urllib.request
try:
    urllib.request.urlopen("http://localhost:8080/health", timeout=3)
except Exception:
    sys.exit(1)
"""


def wait_for_openwebui(timeout=300):
    """Wait until Open WebUI answers its health check, which it only does once
    it has finished starting up (and set up its database)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            exec_python("openwebui", _HEALTH_CHECK)
            return
        except ComposeError:
            time.sleep(3)
    raise ComposeError(f"Open WebUI didn't come up within {timeout} seconds.")
