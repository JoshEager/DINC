"""DINC.py's own small database (dinc/state.db), which remembers what has been
done to this install. Right now that is which migrations have run."""

from contextlib import closing
import sqlite3
import time

from . import paths

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS migrations (
    id         INTEGER NOT NULL,
    phase      TEXT    NOT NULL,
    name       TEXT    NOT NULL,
    applied_at INTEGER NOT NULL,
    PRIMARY KEY (id, phase)
);
"""


def exists():
    return paths.STATE_DB.exists()


def _connect():
    db = sqlite3.connect(paths.STATE_DB)
    db.executescript(_SCHEMA)
    return db


def applied():
    """The set of (migration id, phase) pairs that have run."""
    if not exists():
        return set()
    with closing(_connect()) as db:
        return set(db.execute("SELECT id, phase FROM migrations"))


def history():
    """Every applied migration phase, oldest first, as (id, phase, name, applied_at)."""
    if not exists():
        return []
    with closing(_connect()) as db:
        return list(db.execute(
            "SELECT id, phase, name, applied_at FROM migrations ORDER BY id, applied_at"
        ))


def mark_applied(migration_id, phase, name):
    with closing(_connect()) as db, db:
        db.execute(
            "INSERT OR REPLACE INTO migrations (id, phase, name, applied_at) VALUES (?, ?, ?, ?)",
            (migration_id, phase, name, int(time.time())),
        )


def get_meta(key, default=None):
    if not exists():
        return default
    with closing(_connect()) as db:
        row = db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_meta(key, value):
    with closing(_connect()) as db, db:
        db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, str(value)))
