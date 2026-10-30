# QTs Support — Discord Bot

A Discord bot built with discord.py 2.x, with moderation, welcome messages, voice moderation, server role management, and admin utilities. Anti-Nuke and Automod (anti-spam, anti-link, and mass-ping protection) have been removed; existing JSON settings are retained.

The displayed bot name is **QTs Support**. Keep internal `Dilbar` class and module names for compatibility. The Discord account username is managed separately in Discord; changing source labels does not rename that account. Leave the imported project stopped unless the user asks to run it.

## Run & Operate

- Start the bot in Replit with the **Start Bot** workflow (`python main.py`).
- Dependencies in Replit are managed by Poetry (`pyproject.toml` and `poetry.lock`). Restore them with `poetry install --no-root` on a fresh environment.
- A successful connection logs `Shard ID 0 has connected to Gateway`, followed by `Loaded & Online!`. The Flask keep-alive response alone does not confirm Discord connectivity.
- For local runs, provide `TOKEN` in the environment or a `.env` file, then run `python main.py`.
- On AWS: `bash start.sh`
- With Docker: `docker build -t dilbar . && docker run --env-file .env dilbar`

## Required Environment Variables

In Replit, add `TOKEN` in Tools > Secrets. For local runs, create a `.env` file (copy from `.env.example`):

- `TOKEN` — Discord bot token (required)
- `TOPGG_TOKEN` — Top.gg API token (optional, for voter checks)
- `LAVALINK_PASSWORD` and `SPOTIFY_CLIENT_SECRET` — only required if re-enabling the disabled music cog

## Stack

- Python 3.10
- discord.py 2.x (NOT py-cord; they conflict)
- jishaku (debug extension)
- wavelink (used by the disabled music cog)
- Flask (keep-alive web server on port 8080)
- aiohttp, httpx, psutil, requests

## Where things live

- `main.py` — bot entry point, Flask keep-alive, on_ready
- `core/Dilbar.py` — AutoShardedBot subclass with custom prefix logic
- `core/Context.py` — custom Context with Component V2 auto-conversion
- `cogs/commands/` — all command cogs
- `cogs/events/` — event cogs (logging, welcome, and other active features)
- `utils/` — shared helpers (config, permissions, emojis, tools)
- `config.json` — per-guild settings (prefix, roles)
- `database.json` — per-guild extended data (welcome, autorole, etc.)
- `anti.json` — retained legacy Anti-Nuke settings; no longer used by the bot
- `badges.json` — custom badge data per user

## Architecture decisions

- Uses discord.py 2.x exclusively — do NOT add py-cord to requirements (they clash)
- Intents.all() is required for presences (Spotify) and member_count
- Top.gg token goes in TOPGG_TOKEN env var, NOT hardcoded in source
- Flask runs on PORT env var (defaults 8080) as a keep-alive server
- `asyncio.create_task` used for background tasks — NOT deprecated `loop.create_task`

## AWS Deployment

1. SSH into your EC2 instance
2. `git clone <repo>` or upload files
3. Copy `.env.example` to `.env` and fill in your TOKEN
4. Option A — direct: `bash start.sh`
5. Option B — Docker: `docker build -t dilbar . && docker run -d --env-file .env --restart always dilbar`
6. To run as a service, create `/etc/systemd/system/dilbar.service` (see below)

### systemd service (recommended for AWS)

```ini
[Unit]
Description=QTs Support Discord Bot
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/dilbar
ExecStart=/bin/bash start.sh
Restart=always
RestartSec=5
EnvironmentFile=/home/ec2-user/dilbar/.env

[Install]
WantedBy=multi-user.target
```

Then: `sudo systemctl enable dilbar && sudo systemctl start dilbar`

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Never install both py-cord AND discord.py — they conflict at import level
- `sync_commands` / `sync_commands_debug` kwargs are py-cord only (not discord.py)
- `intents.all()` must be enabled in Discord Developer Portal too
- Emoji IDs in `utils/emojis.py` are custom server emojis — update them to match your bot's server
