"""Every file and folder DINC.py touches, relative to the project folder."""

from pathlib import Path

# The folder DINC.py lives in, no matter where it is run from.
PROJECT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT / ".env"
COMPOSE_FILE = PROJECT / "docker-compose.yml"

# DINC.py's own record of this install (which migrations ran, and when).
STATE_DB = PROJECT / "dinc" / "state.db"

SEARXNG_TEMPLATE = PROJECT / "searxng" / "config" / "settings.yml.template"
SEARXNG_SETTINGS = PROJECT / "searxng" / "config" / "settings.yml"

# Folders the compose file mounts. They are not tracked by git, so they are
# created on install and on every update in case a new one was added.
DATA_DIRS = [
    PROJECT / "openwebui",
    PROJECT / "tailscale" / "state",
    PROJECT / "searxng" / "data",
    PROJECT / "open-terminal",
]


def ensure_data_dirs():
    for directory in DATA_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
