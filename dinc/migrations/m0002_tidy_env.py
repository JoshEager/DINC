"""Drop .env settings that docker-compose.yml now handles itself."""

# WEBUI_TERMINAL_CONNECTIONS: the Open Terminal connection is now written out in
#   docker-compose.yml, using OPEN_TERMINAL_API_KEY.
# WEBUI_PERSIST_CONFIG: Open WebUI always keeps your settings now, and DINC
#   changes them with migrations instead of by turning persistence off.
OLD_KEYS = ("WEBUI_TERMINAL_CONNECTIONS", "WEBUI_PERSIST_CONFIG")

# The comment the old setup.py wrote at the top of .env, which was all about
# WEBUI_PERSIST_CONFIG.
OLD_HEADER = (
    "# If you're chaning an environment variable related to open web ui config, please just don't bother.",
    "# It probably won't update unless you have WEBUI_PERSIST_CONFIG=False set.",
    "# Just change what you want in the web dashboard. If you do set the persist config variable, then you",
    "# should know that any changes you make in the webui will not persist (why it's off by defualt)",
    "# For develpment and testing purposes, WEBUI_PERSIST_CONFIG is nice to make sure your defaults are good.",
)


def prepare(ctx):
    for key in OLD_KEYS:
        if ctx.env.remove(key):
            ctx.log(f"Removed {key} from .env.")

    kept = [line for line in ctx.env.lines if line.rstrip() not in OLD_HEADER]
    if len(kept) != len(ctx.env.lines):
        while kept and not kept[0].strip():
            kept.pop(0)
        ctx.env.lines = kept
        ctx.env.changed = True
