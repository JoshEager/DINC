# DINC is the Easiest Way to Self Host your own Chat-GPT
There are many ways to self host your own chat gpt, but most of them are not very user friendly. Furthermore, if you want to be able to use what you host outside of your home network, you also have to figure out how to expose it to the public internet securely. This project handles most of that setup work for you and is preconfigured with very sensible defaults.

# Quick Start

## Tailscale Setup 
To get started, the first thing you need to do is create a free [tailscale](https://tailscale.com) account if you don't already have one. Follow the guide that they have and add your personal computer to your tailnet, as well as your phone and any other device you would use your chat-gpt from.

Then, you need to generate an auth key. We will use this later in the setup. To do this, go to your [admin dashboard](https://console.tailscale.com) and click Settings>Keys>Generate Auth Key. Add a description and leave everything else default (unless you know what you're doing). Then simply copy the key it generates to your clipboard. Make sure not to lose this key from your clipboard as you won't be able to see it again. If you don't already have clipboard history on, I would recommend turning it on before copying this. If you don't want to do that, you can simply paste it into a text file to be safe.

You may also want to check that MagicDNS is enabled for your tailnet (not required, but nice to have). You also *must* **enable https on your tailnet**. You can do that by going to your [admin dashboard](https://console.tailscale.com) and clicking Settings>General>Https>Enable https 

## Open Router Setup
You're going to want to sign up for [open router](https://openrouter.ai) if you haven't already. It is my recommended way of actually connecting to models that other people host. If you have really good hardware, maybe you could consider modifying this setup to also have an ollama instance to self host your models, though I honestly have been there and don't recommend it for real world chatting.

Next, you'll need to generate an api key for use within Open Web UI. To do this, go to your [open router workspace](https://openrouter.ai/workspaces/default) and click "New Key". Then follow the key creation wizard and copy your key. Later, the setup script for this project will ask for this key and we will paste it in. 

It doesn't cost anything to make a key on open router, and there is a 100% free tier. However, I highly recommend putting at least 10 dollars on your key. Once you do this, your free tier limit actually expands substancially. Also, if you choose the right models, 10 dollars can last you a shockingly long amount of time. 

## Docker Setup
If you don't already have docker installed on whatever machine you are planning on running this stack from, make sure you do that. A convenient guide can be found [here](https://docs.docker.com/engine/install/). You will also need docker compose. For installing docker compose, you can follow the guide [here](https://docs.docker.com/compose/install/) for your platform.

## Project Setup
Clone this repository and run DINC.py. You'll need Python 3.9 or newer, and nothing else to install.
```bash
git clone https://github.com/JoshEager/DINC.git && cd DINC
```
```bash
python DINC.py
```
This opens DINC's menu. Pick **Install**, and it will ask for your tailscale auth key and your open router key (they won't show up as you type or paste, for security reasons), generate every other secret for you, and offer to start the stack. Give it a minute, and your stack will be available at `https://dinc.<your tailnet>.ts.net`.

Every container runs in the same timezone as the machine you installed on. To use a different one, change `TZ` in `.env` to a name from [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (like `America/Detroit`) and run `docker compose up -d`.

# Features
## Open Web UI With Sensible defaults
DINC configures and runs an instance of [Open WebUI](https://github.com/open-webui/open-webui). Open WebUI is essentially a clone of Chat-GPT's frontend, but with way more features and way cooler. It also keeps your chats privately stored on your computer. The features of Open WebUI are almost limitless. 

## Give Your LLMS Their Own Sandboxed Linux Machine
By default, DINC configures and runs [Open Terminal](https://github.com/open-webui/open-terminal) and connects it to Open Web UI through the dedicated terminal integration. Your LLM gets a full Linux environment where it can install its own packages, create files, run code, and even make github PRs if you ask it to. Open Terminal also adds a file browser and an interactive terminal pane to the UI.

## Run Claude Code, Codex, OpenCode, Hermes and More From Your Chat
Open Terminal isn't just a sandbox for your regular models. It can also run full coding agents, and Open WebUI lets you chat with them like any other model. This works through the [Agent Client Protocol](https://agentclientprotocol.com) (ACP), an open standard for how an app talks to an agent. Open Terminal starts the agent's command line tool inside the terminal, Open WebUI speaks ACP to it, and the agent shows up in the model picker as `<agent>/<model>` (for example `opencode/...` or `hermes/...`). You get the agent's own tools, memory and skills, its steps shown as cards in the chat, and its tool approvals as buttons you click. Its workspace is the Open Terminal home folder, so you can watch what it does in the file browser.

Because the agent lives on the Open Terminal machine, DINC doesn't need to run or configure it for you. Install whichever agents you like, and they all work the same way. Open Terminal supports these out of the box ([full list and details](https://docs.openwebui.com/features/open-terminal/agents)):

| Agent | Command it needs on the PATH |
| --- | --- |
| Claude Code | `claude` |
| Codex | `codex` |
| OpenCode | `opencode` |
| Hermes Agent | `hermes` |
| Gemini CLI | `gemini` |
| GitHub Copilot | `copilot` |
| Cursor | `agent` |
| Goose | `goose` |
| Qwen Code | `qwen` |
| Cline | `cline` |
| Grok | `grok` |
| Antigravity | `agy` |
| Pi | `pi` |

### Adding an agent
1. In Open WebUI, open the terminal pane and install the agent using its own install instructions.
2. Log the agent in from that same terminal (for example run `claude` or `codex login --device-auth` and follow the prompts, or give it an API key). If you want it to use your OpenRouter key, most agents accept one in their own config.
3. Start a new chat, select the Open Terminal, and pick the agent from the model picker. If it doesn't show up, run `docker compose restart open-terminal` so Open Terminal finds the new command.

A few things to know:
- **Only your home folder survives.** DINC keeps `/home/user` (the `open-terminal/` folder on your host) across restarts and updates. Anything installed elsewhere, like `apt install` or a system-wide `npm install -g`, is wiped when the container is recreated. Most agent installers put themselves in your home folder already. For npm, run `npm config set prefix ~/.local` first so `npm install -g` lands in `~/.local/bin`.
- **Open Terminal has to be able to find the command.** If the agent is installed somewhere that isn't on Open Terminal's PATH, point it there by adding `OPEN_TERMINAL_<AGENT>_COMMAND` to the `open-terminal` service's environment in `docker-compose.yml`, for example `OPEN_TERMINAL_OPENCODE_COMMAND: "/home/user/.opencode/bin/opencode acp"`.
- **Want Claude Code and Codex preinstalled?** Change the `open-terminal` image to `ghcr.io/open-webui/open-terminal:agents`, which is the same image with those two CLIs included.
- **Agent chats need to be saved chats** (not temporary ones), and each chat can only use one agent.

### Any other ACP agent
Any agent that speaks ACP over stdio works, even if it's not in the list above (OpenClaw, Kiro, Droid and so on). Tell Open Terminal how to start it by adding `OPEN_TERMINAL_ACP_AGENTS` to the `open-terminal` service's environment, then run `docker compose up -d open-terminal`:
```yaml
      OPEN_TERMINAL_ACP_AGENTS: '{"kiro":{"name":"Kiro","command":"kiro-cli acp"}}'
```
Check the agent's docs for the command that starts it in ACP mode. It shows up in the model picker as `acp-<id>/<model>`.

### Hermes and other always-on agents
Some agents, like Hermes, can also run as a long-lived assistant that you message from Telegram, Discord, Slack and other chat apps. You can set that up on the Open Terminal machine too, following the agent's own docs, and it will keep the same memory whether you talk to it there or in Open WebUI.

# Managing Your Install
Run `python DINC.py` any time for the menu. It shows whether the stack is running and whether an update is waiting, and lets you:

- **Update:** pulls the latest DINC, runs any migrations, pulls new images, and restarts the stack.
- **Status:** shows every service and which migrations have run.
- **Start, Stop, Restart, Logs:** the everyday docker compose commands, without having to remember them.
- **Change OpenRouter key:** swaps your key in `.env` *and* in Open WebUI.

Every menu item also works as a command, which is handy for scripts and cron. For example:
```bash
python DINC.py update
```
Run `python DINC.py --help` for the full list.

## How updates work
Open WebUI only reads most of its settings from `docker-compose.yml` the very first time it starts. After that it keeps them in its own database, which is how your changes in the admin panel stick (a connection you added, a feature you turned off). It also means a new default in `docker-compose.yml` never reaches an install that already exists.

So when a new version of DINC needs to change something on an existing install, it ships a *migration*. A migration can edit `.env` and other files before the stack starts, and change individual Open WebUI settings once it's running. It only touches the settings it's about, so everything you've changed yourself stays as it is. Each migration runs once per install, and DINC.py remembers which ones have run in `dinc/state.db`, so if you undo something a migration did, it stays undone. Before changing Open WebUI's settings, DINC.py backs up its database to `openwebui/dinc-backups/`.

## Working on DINC.py
`DINC.py` only starts the code in the `dinc/` folder:

| Path | What it does |
| --- | --- |
| `dinc/app.py` | The menu and the command line |
| `dinc/commands/` | One file per area: install, update, status, services, settings. Register new commands in `commands/__init__.py`, which adds them to the menu and command line at once |
| `dinc/migrations/` | One file per migration (`m0003_short_name.py`). How to write one is explained at the top of `migrations/__init__.py` |
| `dinc/openwebui.py` | Reads and changes Open WebUI settings inside the running container |
| `dinc/compose.py`, `envfile.py`, `state.py` | docker compose, the `.env` file, and `dinc/state.db` |

The one rule to remember: when you change a default, change it in two places. Put it in `docker-compose.yml` (or the install command) for new installs, and in a migration for existing ones. New installs mark every migration as done, because they already start out current.

# License
The MIT License (MIT)

Copyright (c) 2026 Josh Eager

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
