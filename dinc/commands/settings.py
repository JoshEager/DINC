"""Changing settings that live in both .env and Open WebUI's database."""

from .. import compose, openwebui, paths, ui
from ..envfile import EnvFile

OPENROUTER = "openrouter.ai"


def _swap_openrouter_key(new_key):
    """Point every OpenRouter connection in Open WebUI at new_key. Returns how
    many it changed."""
    current = openwebui.get("openai.api_base_urls", "openai.api_keys", "images.connections")
    updates, changed = {}, 0

    urls = current.get("openai.api_base_urls", [])
    keys = list(current.get("openai.api_keys", []))
    for i, url in enumerate(urls):
        if OPENROUTER in url and i < len(keys):
            keys[i] = new_key
            changed += 1
    updates["openai.api_keys"] = keys

    images = current.get("images.connections", [])
    for connection in images:
        if OPENROUTER in connection.get("url", ""):
            connection["key"] = new_key
            changed += 1
    updates["images.connections"] = images

    if changed:
        openwebui.set(updates)
    return changed


def openrouter_key(args):
    if not paths.ENV_FILE.exists():
        ui.warn("DINC isn't installed here yet. Run Install first.")
        return 1

    ui.heading("Change your OpenRouter key")
    new_key = ui.ask_secret("New OpenRouter API key")

    env = EnvFile(paths.ENV_FILE)
    env.set("OPENROUTER_API_KEY", new_key)
    env.save()
    ui.ok("Saved it to .env.")

    # Open WebUI copied the old key into its database on first launch, and that
    # copy is the one it uses, so it has to change there too.
    if not compose.is_running(openwebui.SERVICE):
        if not ui.confirm("Open WebUI has to be running to change the key there too. Start the stack?"):
            ui.warn("Open WebUI is still using the old key. Run this again once it's running.")
            return 1
        compose.run("up", "-d")
    compose.wait_for_openwebui()
    changed = _swap_openrouter_key(new_key)
    if changed:
        ui.ok(f"Updated {changed} OpenRouter connection{'s' if changed != 1 else ''} in Open WebUI.")
    else:
        ui.warn("Didn't find any OpenRouter connections in Open WebUI. Check Admin Settings > Connections.")
    return 0
