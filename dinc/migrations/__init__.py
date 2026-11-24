"""Migrations bring an existing install up to date with the current version of
DINC. Each one runs once per install, and dinc/state.db remembers which have run.

Writing one
-----------
Add a file named mNNNN_short_name.py to this folder, numbered one past the
newest. Give it a docstring (its first line is shown when it runs) and one or
both of these functions, which receive a Context:

    def prepare(ctx):
        # Runs before the containers start. Edit ctx.env (the .env file, saved
        # for you afterwards) or files under ctx.project.

    def openwebui(ctx):
        # Runs once Open WebUI is up. Change its settings with
        # ctx.openwebui.get(...) and ctx.openwebui.set({...}).

Rules of thumb:
- Change only what you need to, and merge into lists instead of replacing
  them, so settings people changed themselves survive.
- Make it safe to run twice. Installs from before dinc/state.db existed run
  every migration once.
- Put the same change in docker-compose.yml (or the install command) too.
  A fresh install skips every migration that exists when it is installed,
  because it starts out current. dinc/state.db stores the newest migration at
  that point as the install's baseline, and only migrations after it ever run.
"""

from dataclasses import dataclass, field
import importlib
import pkgutil
import re
from types import ModuleType

from .. import openwebui, paths, state, ui
from ..envfile import EnvFile

PHASES = ("prepare", "openwebui")

_NAME = re.compile(r"^m(\d{4})_(\w+)$")


@dataclass
class Migration:
    id: int
    name: str
    module: ModuleType

    @property
    def description(self):
        doc = (self.module.__doc__ or self.name).strip()
        return doc.splitlines()[0]

    @property
    def phases(self):
        return [phase for phase in PHASES if hasattr(self.module, phase)]


@dataclass
class Context:
    env: EnvFile
    project: object = paths.PROJECT
    openwebui: ModuleType = openwebui
    log: object = field(default=ui.info)


def discover():
    """Every migration in this folder, oldest first."""
    found = []
    for module_info in pkgutil.iter_modules(__path__):
        match = _NAME.match(module_info.name)
        if match:
            module = importlib.import_module(f"{__name__}.{module_info.name}")
            found.append(Migration(int(match.group(1)), match.group(2), module))
    found.sort(key=lambda m: m.id)
    ids = [m.id for m in found]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Two migrations share a number. Renumber one of them.")
    return found


def baseline():
    """The newest migration this install started out past (0 if none)."""
    return int(state.get_meta("baseline", 0))


def pending(phase=None):
    """(migration, phase) pairs that haven't run yet, in order."""
    done = state.applied()
    start = baseline()
    return [
        (migration, p)
        for migration in discover()
        if migration.id > start
        for p in migration.phases
        if (phase is None or p == phase) and (migration.id, p) not in done
    ]


def run(phase):
    """Run every pending migration for one phase. Each is recorded as soon as it
    finishes, so if one fails, the ones before it don't run again next time."""
    todo = pending(phase)
    for migration, p in todo:
        ui.info(f"Migration {migration.id:04d}: {migration.description}")
        ctx = Context(env=EnvFile(paths.ENV_FILE))
        getattr(migration.module, p)(ctx)
        ctx.env.save()
        state.mark_applied(migration.id, p, migration.name)
    return len(todo)


def set_baseline():
    """Used by a fresh install, which already includes every migration so far.
    Nothing is written to the migrations table, which only lists ones that ran."""
    found = discover()
    state.set_meta("baseline", found[-1].id if found else 0)
