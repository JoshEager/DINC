"""
To get start playing with your dinc, simply run this python script and it will
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
import json
import sys

# Make sure that no matter where the script is being ran from, it always works relative
# to the parent directory of where the script lives
project_dir = Path(__file__).resolve().parent

# These are directories that are needed for the compose file and are NOT tracked by git
directories = [
    "openwebui", 
    "tailscale/state",
    "searxng/data",
    "valkey/data",
    "mcpo/workspace"
]
for directory in directories:
    (project_dir / directory).mkdir(parents=True, exist_ok=True)


ts_auth_key = getpass("Paste your tailscale auth key: ").strip()
if not ts_auth_key:
    print("Auth key must not be of length zero!")
    sys.exit(1)
openrouter_api_key = getpass("Paste your OpenRouter API key: ").strip()
if not openrouter_api_key:
    print("Open router api key must not be of length zero!")
    sys.exit(1)
image_gen_model = input("Image generation model (blank for default of meta/muse-image, configurable in openwebui): ").strip()
if not image_gen_model:
    image_gen_model = "meta/muse-image"
project_name = input("Project name (for docker compose): ") # Project name are important if you host more than one instance of dinc
if not project_name:
    print("You must provide a project name!")
    sys.exit(1)

webui_secret_key = token_hex(32)
searxng_secret_key = token_hex(32)
mcpo_api_key = token_hex(32)

webui_tool_connections = json.dumps([
  {
    "type": "openapi",
    "url": "http://mcpo:8000/bash",
    "spec_type": "url",
    "spec": "",
    "path": "openapi.json",
    "auth_type": "bearer",
    "key": f"{mcpo_api_key}",
    "config": { "enable": "true" },
    "info": {
      "id": "",
      "name": "Bash",
      "description": "Gives an agent the ability to run bash commands on its own machine."
    }
  }
], indent=None)


env_contents = (
    "# If you're chaning an environment variable related to open web ui config, please just don't bother.\n"
    "# It probably won't update unless you have WEBUI_PERSIST_CONFIG=False set. \n"
    "# Just change what you want in the web dashboard. If you do set the persist config variable, then you\n"
    "# should know that any changes you make in the webui will not persist (why it's off by defualt)\n"
    "# For develpment and testing purposes, WEBUI_PERSIST_CONFIG is nice to make sure your defaults are good.\n"
    "\n"
    f"TS_AUTHKEY={ts_auth_key}\n"
    f"WEBUI_SECRET_KEY={webui_secret_key}\n"
    f"OPENROUTER_API_KEY={openrouter_api_key}\n"
    f"IMAGE_GEN_MODEL={image_gen_model}\n"
    f"PROJECT_NAME={project_name}\n"
    f"MCPO_API_KEY={mcpo_api_key}\n"
    f"WEBUI_TOOL_CONNECTIONS='{webui_tool_connections}'\n"
    "WEBUI_PERSIST_CONFIG=True\n"
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

