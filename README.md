# DINC is the Easiest Way to Self Host your own Chat-GPT
There are many ways to self host your own chat gpt, but most of them are not very user friendly. Furthermore, if you want to be able to use what you host outside of your home network, you also have to figure out how to expose it to the public internet securely. This project handles most of that setup work for you and is preconfigured with very sensible defaults.

# Quick Start

## Tailscale Setup 
To get started, the first thing you need to do is create a free [tailscale](https://tailscale.com) account if you don't already have one. Follow the guide that they have and add your personal computer to your tailnet, as well as your phone and any other device you would use your chat-gpt from.

Then, you need to generate an auth key. We will use this later in the setup. To do this, go to your [admin dashboard](https://console.tailscale.com) and click Settings>Keys>Generate Auth Key. Add a description and leave everything else default (unless you know what you're doing). Then simply copy the key it generates to your clipboard. Make sure not to lose this key from your clipboard as you won't be able to see it again. If you don't already have clipboard history on, I would recommend turning it on before copying this. If you don't want to do that, you can simply paste it into a text file to be safe.

You may also want to check that MagicDNS is enabled for your tailnet (not required, but nice to have).

## Open Router Setup
You're going to want to sign up for [open router](https://openrouter.ai) if you haven't already. It is my recommended way of actually connecting to models that other people host. If you have really good hardware, maybe you could consider modifying this setup to also have an ollama instance to self host your models, though I honestly have been there and don't recommend it for real world chatting.

Next, you'll need to generate an api key for use within Open Web UI. To do this, go to your [open router workspace](https://openrouter.ai/workspaces/default) and click "New Key". Then follow the key creation wizard and copy your key. Later, the setup script for this project will ask for this key and we will paste it in. 

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
The script will ask for your tailscale auth key. Please note that it will not show up when you type (or paste) for security reasons. 
After running the setup script, all you need to do is run the following command, and your stack should be available at `https://dinc.<your tailnet>.ts.net`
```bash
docker compose up -d
``` 

# Features