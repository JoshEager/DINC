"""Reading and editing the .env file without losing comments or ordering."""

import re

# Values made only of these characters are written bare. Anything else is
# single quoted, which docker compose reads literally (no $ expansion).
_SAFE = re.compile(r"^[A-Za-z0-9_./:@+-]*$")


def _unquote(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def _quote(value):
    if _SAFE.match(value):
        return value
    if "'" in value:
        raise ValueError("Values in .env can't contain a single quote (').")
    return f"'{value}'"


def _key_of(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    return stripped.split("=", 1)[0].strip()


class EnvFile:
    """An .env file held as its lines. Edits change lines in place, new keys go
    at the end, and nothing is written until save() is called."""

    def __init__(self, path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        self.changed = False

    def _index(self, key):
        for i, line in enumerate(self.lines):
            if _key_of(line) == key:
                return i
        return None

    def __contains__(self, key):
        return self._index(key) is not None

    def get(self, key, default=None):
        i = self._index(key)
        if i is None:
            return default
        return _unquote(self.lines[i].split("=", 1)[1])

    def set(self, key, value):
        line = f"{key}={_quote(str(value))}"
        i = self._index(key)
        if i is None:
            self.lines.append(line)
        elif self.lines[i] == line:
            return
        else:
            self.lines[i] = line
        self.changed = True

    def set_default(self, key, value):
        """Set key only if it is missing or blank. Returns True if it was set."""
        if self.get(key):
            return False
        self.set(key, value)
        return True

    def remove(self, key):
        """Remove key. Returns True if it was there."""
        i = self._index(key)
        if i is None:
            return False
        del self.lines[i]
        self.changed = True
        return True

    def save(self):
        if not self.changed:
            return False
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        self.changed = False
        return True
