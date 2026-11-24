"""Remove Hermes (agents now run inside Open Terminal)."""

HERMES_KEYS = (
    "HERMES_API_KEY",
    "HERMES_UID",
    "HERMES_GID",
    "HERMES_DASHBOARD_USERNAME",
    "HERMES_DASHBOARD_PASSWORD",
    "HERMES_DASHBOARD_SECRET",
)


def prepare(ctx):
    for key in HERMES_KEYS:
        if ctx.env.remove(key):
            ctx.log(f"Removed {key} from .env.")


def openwebui(ctx):
    # Drop the OpenAI connection that pointed at the Hermes container. Open
    # WebUI keeps its connections as parallel lists of urls and keys, plus a
    # dict of per connection settings keyed by list position (or sometimes by
    # url), so all three have to shift together.
    current = ctx.openwebui.get("openai.api_base_urls", "openai.api_keys", "openai.api_configs")
    urls = current.get("openai.api_base_urls", [])
    keys = current.get("openai.api_keys", [])
    configs = current.get("openai.api_configs", {})

    keep = [i for i, url in enumerate(urls) if "hermes:8642" not in url]
    if len(keep) == len(urls):
        return

    new_configs = {}
    for new, old in enumerate(keep):
        if str(old) in configs:
            new_configs[str(new)] = configs[str(old)]
        if urls[old] in configs:
            new_configs[urls[old]] = configs[urls[old]]

    ctx.openwebui.set({
        "openai.api_base_urls": [urls[i] for i in keep],
        "openai.api_keys": [keys[i] if i < len(keys) else "" for i in keep],
        "openai.api_configs": new_configs,
    })
    ctx.log("Removed the Hermes connection from Open WebUI.")
