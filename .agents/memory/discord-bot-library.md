---
name: Discord bot library setup
description: This bot uses discord.py 2.x exclusively. py-cord was listed in requirements by mistake and conflicts.
---

## Rule
Use discord.py 2.6 or newer, below 3 — NOT py-cord. A development Git checkout is not required.

**Why:** The codebase uses discord.py 2.x-only APIs: `commands.hybrid_command`, `discord.TextStyle`, `app_commands`. py-cord is a fork that diverged and does not have these. Both install to the same `discord` namespace so they cannot coexist.

**How to apply:** Never add `py-cord` to requirements. Resolve dependent libraries together with discord.py constrained to a compatible version; modern released versions support Component V2.

## Other packages required (not in discord.py itself)
- `discord-ext-menus==1.1` — for `discord.ext.menus` (paginators)
- `discord-games` — for `discord_games` import in Games cog
- `reactionmenu` — used in some cogs
- `tasksio` — used in event cogs
- `jishaku` — modern released versions are compatible with discord.py 2.6+
