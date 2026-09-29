"""
To get started with your own ai-stack, simply run this python script and it will
guide you through the process. 

It starts by making the directory structure required for docker compose. Then,
it will prompt you for your tailscale auth key. If you don't know how to create
a tailscale auth key, then you refer to the readme for a quick guide. 

The script will also take care of generating all of your secrets and storing them
in a .env file. 
"""

from getpass import getpass
from pathlib import Path
from secrets import token_hex
import sys

# Make sure that no matter where the script is being ran from, it always works relative
# to the parent directory of where the script lives
project_dir = Path(__file__).resolve().parent

# These are directories that are needed for the compose file and are NOT tracked by git
directories = [
    "openwebui", 
    "tailscale/state",
    "searxng/data",
    "valkey/data"
]
for directory in directories:
    (project_dir / directory).mkdir(parents=True, exist_ok=True)


ts_auth_key = getpass("Paste your tailscale auth key: ").strip()
if not ts_auth_key:
    print("Auth key must not be of length zero!")
    sys.exit(1)


webui_secret_key = token_hex(32)
searxng_secret_key = token_hex(32)


env_contents = (
    f"TS_AUTHKEY={ts_auth_key}\n"
    f"WEBUI_SECRET_KEY={webui_secret_key}\n"
)
env_file = project_dir / ".env"
if env_file.exists():
    print("Env file already exists! It was left unchanged.")
    sys.exit(1)
with env_file.open('x', encoding="utf-8") as f:
    f.write(env_contents)


# The searxng secret key does not support being loaded via environment variables.
# Therefore, we need to create an untracked settings.yml that has the secret key 
# using the settings.yml.template file. 
searxng_settings_template_file = (project_dir / "searxng" / "config" / "settings.yml.template").read_text(encoding="utf-8")
searxng_settings_file = project_dir / "searxng" / "config" / "settings.yml"
if searxng_settings_file.exists():
    print("Searxng's settings.yml file already exists. Will not overwrite it!")
    sys.exit(1)

settings = searxng_settings_template_file.replace("___SEARXNG_SECRET_KEY___", searxng_secret_key)
searxng_settings_file.write_text(settings, encoding="utf-8")

