"""Working out which timezone the machine running DINC is set to."""

import os
from pathlib import Path

FALLBACK = "UTC"


def _is_valid(name):
    try:
        from zoneinfo import available_timezones
    except ImportError:
        return True
    zones = available_timezones()
    # Without tzdata (bare Windows Python) the list is empty, so trust the name.
    return not zones or name in zones


def _candidates():
    # Someone may have set TZ for their shell on purpose, so it comes first.
    yield os.environ.get("TZ", "").lstrip(":")

    # Debian and Ubuntu write the name to /etc/timezone.
    timezone_file = Path("/etc/timezone")
    if timezone_file.is_file():
        yield timezone_file.read_text(encoding="utf-8").strip()

    # Most other Linux distros, and macOS, symlink /etc/localtime to the zone's
    # file, e.g. /usr/share/zoneinfo/America/Detroit.
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        target = str(localtime.resolve())
        if "zoneinfo/" in target:
            yield target.split("zoneinfo/", 1)[1]


def detect():
    """The machine's timezone name, like "America/Detroit", or UTC if it can't
    be worked out."""
    for name in _candidates():
        # Real zone names look like Area/City. That also skips things like
        # "EST5EDT" that some systems put in TZ.
        if ("/" in name or name == FALLBACK) and _is_valid(name):
            return name
    return FALLBACK
