---
name: Replit Python dependency setup
description: Git dependencies can fail under the imported Poetry environment; prefer compatible registry releases.
---

Use compatible registry releases rather than Git dependencies when a development checkout is not necessary.

**Why:** The Replit package installer attempted to clone Git dependencies into a read-only Nix Python prefix and failed with permission denied. Resolving released discord.py and jishaku versions together succeeded; the prior assumption that separate installation order was required no longer applies to these releases.

**How to apply:** Use the package-management tools with registry package versions. Retain discord.py >=2.6 for Component V2 support. If using TOML, quote package keys containing dots so they are not interpreted as nested tables.
