"""First time setup: ask for your keys, generate every secret, and write .env."""

from secrets import token_hex
import time

from .. import compose, migrations, paths, state, timezone, ui

DEFAULT_IMAGE_MODEL = "meta/muse-image"

HEADER = """\
# DINC's settings, written by `python DINC.py install`.
# Most of these only matter the first time the stack starts. After that, Open
# WebUI keeps its settings in its own database, so change them in its admin
# panel (or with DINC.py, for the ones it has a menu entry for).
"""


def write_searxng_settings():
    # SearXNG can't take its secret key from an environment variable, so it
    # gets its own untracked copy of the settings template with a key filled in.
    if paths.SEARXNG_SETTINGS.exists():
        ui.info("SearXNG's settings.yml already exists, leaving it alone.")
        return
    template = paths.SEARXNG_TEMPLATE.read_text(encoding="utf-8")
    paths.SEARXNG_SETTINGS.write_text(
        template.replace("___SEARXNG_SECRET_KEY___", token_hex(32)), encoding="utf-8"
    )
    ui.ok("Wrote searxng/config/settings.yml.")


def run(args):
    if paths.ENV_FILE.exists():
        ui.warn("DINC is already installed here (there's a .env file). Use Update instead.")
        return 1

    ui.heading("Installing DINC")
    print("You'll need your Tailscale auth key and OpenRouter API key. The README")
    print("explains how to get both. Keys are hidden as you type or paste them.\n")

    tailscale_key = ui.ask_secret("Tailscale auth key")
    openrouter_key = ui.ask_secret("OpenRouter API key")
    image_model = ui.ask("Image generation model", default=DEFAULT_IMAGE_MODEL)
    # The compose project name keeps containers apart if you run more than one
    # DINC on the same machine.
    project_name = ui.ask("Project name for docker compose", default="dinc")
    tz = timezone.detect()

    env = "\n".join([
        HEADER,
        f"PROJECT_NAME={project_name}",
        f"TS_AUTHKEY={tailscale_key}",
        f"OPENROUTER_API_KEY={openrouter_key}",
        f"IMAGE_GEN_MODEL={image_model}",
        f"TZ={tz}",
        f"WEBUI_SECRET_KEY={token_hex(32)}",
        f"OPEN_TERMINAL_API_KEY={token_hex(32)}",
    ]) + "\n"
    with paths.ENV_FILE.open("x", encoding="utf-8") as f:
        f.write(env)
    ui.ok("Wrote .env with your keys and freshly generated secrets.")
    ui.info(f"Set the stack's timezone to {tz}, the same as this machine. To use a")
    ui.info("different one, change TZ in .env and run `docker compose up -d`.")

    write_searxng_settings()
    paths.ensure_data_dirs()

    # A new install is already current, so no migration needs to run on it.
    migrations.set_baseline()
    state.set_meta("installed_at", int(time.time()))
    ui.ok("DINC is installed.")

    if compose.available() and ui.confirm("\nStart the stack now?"):
        compose.run("up", "-d")
        ui.ok("Started. Give it a minute, then open https://dinc.<your tailnet>.ts.net")
    else:
        ui.info("Start it whenever you're ready with `docker compose up -d` (or Start in DINC.py).")
    return 0
