"""
To get start playing with your dinc, simply run this python script and it will
guide you through the process. 

It starts by making the directory structure required for docker compose. Then,
it will prompt you for your tailscale auth key. If you don't know how to create
a tailscale auth key, then you refer to the readme for a quick guide. 

The script will also take care of generating all of your secrets and storing them
in a .env file. 

If a .env file already exists, the script will instead migrate it in place with
any settings that newer versions of dinc need. 
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
    "mcpo/workspace",
    "open-terminal"
]
for directory in directories:
    (project_dir / directory).mkdir(parents=True, exist_ok=True)

env_file = project_dir / ".env"


def tool_connections_json(mcpo_api_key):
    return json.dumps([
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
          "name": "MCP Manager",
          "description": "A bash environment from which the any LLM can manage the mcp servers exposed by mcpo. "
        }
      }
    ], indent=None)


def terminal_connections_json(open_terminal_api_key):
    return json.dumps([
      {
        "id": "open-terminal",
        "url": "http://open-terminal:8000",
        "key": f"{open_terminal_api_key}",
        "name": "Open Terminal",
        "auth_type": "bearer",
        "config": { "access_grants": [] }
      }
    ], indent=None)


def parse_env_file(path):
    # Returns a dict of key -> raw value (everything after the first =). Comment
    # and blank lines are left out since they never need to be touched.
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        entries[key] = value
    return entries


def unquote(value):
    # Values like the json connection lists are stored wrapped in single quotes
    # so docker compose does not mangle them. Strip them back off for parsing.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def quote(value):
    return f"'{value}'"


def migrate_env_file(path):
    entries = parse_env_file(path)
    changes = []

    open_terminal_api_key = entries.get("OPEN_TERMINAL_API_KEY")
    if not open_terminal_api_key:
        open_terminal_api_key = token_hex(32)
        entries["OPEN_TERMINAL_API_KEY"] = open_terminal_api_key
        changes.append("added OPEN_TERMINAL_API_KEY")

    if "WEBUI_TERMINAL_CONNECTIONS" not in entries:
        entries["WEBUI_TERMINAL_CONNECTIONS"] = quote(terminal_connections_json(open_terminal_api_key))
        changes.append("added WEBUI_TERMINAL_CONNECTIONS")

    # Older env files registered the mcpo tool connection under the name "Bash".
    # Rename it to MCP Manager so it is clear what it is for.
    raw_tool_connections = entries.get("WEBUI_TOOL_CONNECTIONS")
    if raw_tool_connections:
        try:
            connections = json.loads(unquote(raw_tool_connections))
        except json.JSONDecodeError:
            print("Could not parse WEBUI_TOOL_CONNECTIONS! It was left unchanged.")
        else:
            renamed = False
            for connection in connections:
                info = connection.get("info", {})
                if info.get("name") == "Bash":
                    info["name"] = "MCP Manager"
                    info["description"] = "Manages the model's MCP servers and provides a sandboxed bash shell for running commands."
                    renamed = True
            if renamed:
                entries["WEBUI_TOOL_CONNECTIONS"] = quote(json.dumps(connections, indent=None))
                changes.append("renamed the Bash tool connection to MCP Manager")

    if not changes:
        print("Env file is already up to date! It was left unchanged.")
        return

    # Rebuild the file line by line so comments, ordering and any settings we do
    # not know about are preserved. Anything new is appended at the end.
    new_lines = []
    written = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0]
            if key in entries:
                new_lines.append(f"{key}={entries[key]}")
                written.add(key)
                continue
        new_lines.append(line)
    for key, value in entries.items():
        if key not in written:
            new_lines.append(f"{key}={value}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    for change in changes:
        print(f"Migrated .env: {change}.")


# If an env file already exists we are upgrading an existing dinc install. Migrate
# it in place instead of walking through the first time setup prompts again.
if env_file.exists():
    migrate_env_file(env_file)
    sys.exit(0)


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
open_terminal_api_key = token_hex(32)

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
    f"OPEN_TERMINAL_API_KEY={open_terminal_api_key}\n"
    f"WEBUI_TOOL_CONNECTIONS='{tool_connections_json(mcpo_api_key)}'\n"
    f"WEBUI_TERMINAL_CONNECTIONS='{terminal_connections_json(open_terminal_api_key)}'\n"
    "WEBUI_PERSIST_CONFIG=True\n"
)
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
