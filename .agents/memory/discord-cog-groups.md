---
name: discord.py Cog slash-group registration
description: Avoid duplicate app-command registration when adding a cog that declares a Group.
---

# Rule

When a `discord.app_commands.Group` is declared as a cog class attribute, let `Bot.add_cog()` register it; do not also call `tree.add_command()` manually from `cog_load`.

**Why:** discord.py automatically registers cog application commands during injection. Manual registration first raises `CommandAlreadyRegistered` and prevents the cogs extension from loading.

**How to apply:** For grouped slash commands defined on cogs, check for explicit tree registration calls; only manually register groups that are not managed by a Cog.
