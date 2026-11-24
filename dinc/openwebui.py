"""Reading and changing Open WebUI's settings on a running install.

Open WebUI only reads most settings from its environment variables the very
first time it starts. After that each setting lives as its own row in the
`config` table of its database (keys like "terminal_server.connections"), and
whatever is there wins. That is what lets your changes in the admin panel stick,
but it also means changing docker-compose.yml does nothing to an existing
install.

So when DINC needs to change a setting on an existing install, it edits just
that row, from inside the openwebui container (where the database and a Python
with sqlite already are). Every other setting, including anything you changed
yourself, is left alone. Open WebUI reads settings from the database each time
it uses them, so changes apply without a restart.
"""

import json

from . import compose

SERVICE = "openwebui"

# Runs inside the container. DINC_REQUEST is filled in below with a JSON
# request, which keeps secrets out of the command line.
_SCRIPT = r"""
import json, os, sqlite3, sys, time

request = json.loads(DINC_REQUEST)
data_dir = os.environ.get("DATA_DIR", "/app/backend/data")
db = sqlite3.connect(os.path.join(data_dir, "webui.db"))

tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
columns = {row[1] for row in db.execute("PRAGMA table_info(config)")} if "config" in tables else set()
if not {"key", "value"} <= columns:
    sys.exit("Open WebUI's config table isn't laid out the way DINC expects "
             "(one row per key). It may have changed in a newer Open WebUI.")

action = request["action"]
if action == "get":
    keys = request["keys"]
    marks = ",".join("?" * len(keys))
    rows = db.execute(f"SELECT key, value FROM config WHERE key IN ({marks})", keys)
    print(json.dumps({key: json.loads(value) for key, value in rows}))

elif action == "set":
    now = int(time.time())
    with db:
        for key, value in request["values"].items():
            db.execute(
                "INSERT INTO config (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                (key, json.dumps(value), now),
            )
    print("{}")

elif action == "backup":
    folder = os.path.join(data_dir, "dinc-backups")
    os.makedirs(folder, exist_ok=True)
    name = time.strftime("webui-%Y%m%d-%H%M%S.db")
    with sqlite3.connect(os.path.join(folder, name)) as copy:
        db.backup(copy)
    print(json.dumps({"path": "openwebui/dinc-backups/" + name}))
"""


class OpenWebUIError(RuntimeError):
    pass


def _call(request):
    script = f"DINC_REQUEST = {json.dumps(json.dumps(request))}\n{_SCRIPT}"
    try:
        output = compose.exec_python(SERVICE, script)
    except compose.ComposeError as e:
        raise OpenWebUIError(str(e)) from e
    return json.loads(output.strip().splitlines()[-1])


def get(*keys):
    """Return {key: value} for the keys that have a row. Missing keys are left out."""
    return _call({"action": "get", "keys": list(keys)})


def set(values):
    """Write each key in values, creating its row if needed."""
    _call({"action": "set", "values": values})


def backup():
    """Copy the database to openwebui/dinc-backups/ and return that path."""
    return _call({"action": "backup"})["path"]
