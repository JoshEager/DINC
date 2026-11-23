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
All you need to do to setup this project is clone this repository and run setup.py
```bash
git clone https://github.com/JoshEager/DINC.git && cd DINC
```
```bash
python setup.py
```
The script will ask for your tailscale auth key as well as your open router auth key. Please note that it will not show up when you type (or paste) for security reasons. 
After running the setup script, all you need to do is run the following command, and your stack should be available at `https://dinc.<your tailnet>.ts.net`
```bash
docker compose up -d
``` 

# Features
## Open Web UI With Sensible defaults
DINC configures and runs an instance of [Open WebUI](https://github.com/open-webui/open-webui). Open WebUI is essentially a clone of Chat-GPT's frontend, but with way more features and way cooler. It also keeps your chats privately stored on your computer. The features of Open WebUI are almost limitless. 

## Give Your LLMS Their Own Sandboxed Linux Machine
By default, DINC configures and runs [Open Terminal](https://github.com/open-webui/open-terminal) and connects it to Open Web UI through the dedicated terminal integration. Your LLM gets a full Linux environment where it can install its own packages, create files, run code, and even make github PRs if you ask it to. Open Terminal also adds a file browser and an interactive terminal pane to the UI.

## Meet Copper, Your Own AI Agent
DINC ships with Copper, an agent built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) from Nous Research. Pick **Copper** in Open WebUI's model selector and you are talking to a full agent rather than a bare LLM: it has its own tools, remembers things about you and your projects, and builds up skills over time. Copper is named after Michigan's Copper Country, and after the wire everything else runs on.

Copper runs on DeepSeek V4.1 Flash through your OpenRouter key, which is cheap and handles tool use well. Its API is only reachable from inside the stack, not on your tailnet.

Copper is set up exactly the way you would set up an agent of your own, so it doubles as an example. Hermes calls each agent a profile, and Copper's lives in `hermes/profiles/copper/`. You can make Copper your own by editing these files and running `docker compose restart hermes`:

- `config.yaml`: the model. Use any OpenRouter model slug under `model:` > `default:`.
- `SOUL.md`: Copper's personality and instructions.
- `.env`: the name shown in Open WebUI (`API_SERVER_MODEL_NAME`) and the key Open WebUI uses to reach it (`API_SERVER_KEY`).

The originals live in the `copper/` folder. Setup copies them into `hermes/profiles/copper/` once and never overwrites your edits, so to start over, delete a file there and run `python setup.py` again.

### Adding Your Own Agents
Each agent is a folder under `hermes/profiles/<name>/` with its own config, personality, memory, and skills. One Hermes container serves all of them, so you don't need to touch the compose file. The easiest way to make one is to start from Copper's files. For an agent called `coder`:

1. Copy Copper's original files into a new profile folder:
   ```bash
   mkdir -p hermes/profiles/coder && cp copper/config.yaml copper/SOUL.md copper/.env hermes/profiles/coder/
   ```
2. Edit them: rewrite `SOUL.md` so it doesn't think it's Copper, pick a model in `config.yaml`, and change `API_SERVER_MODEL_NAME` in `.env`.
3. Add your `HERMES_API_KEY` (from DINC's `.env`) to the bottom of `hermes/profiles/coder/.env` as `API_SERVER_KEY=<your key>`.
4. Restart Hermes with `docker compose restart hermes`.
5. In Open WebUI, go to Admin Settings > Connections and add an OpenAI connection with URL `http://hermes:8642/p/coder/v1` and your `HERMES_API_KEY` as the key.

Every agent you add is reached at `http://hermes:8642/p/<name>/v1` and shows up as a separate model in the picker. Copy Copper's original files from `copper/` rather than the `hermes/profiles/copper/` folder, since the latter also holds Copper's memories and chat history.

If all you want is different models for different kinds of work, you may not need multiple agents. Hermes can hand subtasks off to child agents with its `delegate_task` tool, and those children can run on a cheaper model. Set it in the agent's `config.yaml`:
```yaml
delegation:
  provider: "openrouter"
  model: "<provider/model>"
```
Separate profiles make more sense when you want agents with different personalities or memories, like one for coding and one for school.

# Upgrading an Existing Install
Pull the latest changes and run the setup script again. When it finds an existing `.env`, it migrates it in place instead of starting over.
```bash
git pull && python setup.py && docker compose up -d --remove-orphans
```
Open WebUI only reads its connection settings from the environment on first launch, so on an existing install you need to add Copper yourself under Admin Settings > Connections > OpenAI: URL `http://hermes:8642/p/copper/v1`, and the `HERMES_API_KEY` value from your `.env` as the key.

If you used an older version with the MCP Manager tool, you can delete it from Open WebUI under Admin Settings > External Tools, along with the leftover `mcpo/` folder.

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
