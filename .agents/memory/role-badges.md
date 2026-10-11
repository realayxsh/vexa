---
name: Role-derived badges
description: How server roles and their icons appear in the bot's badges command.
---

The `/badges` command should include only the target member's current-server roles with `role.hoist` enabled (Discord's “Display role members separately from online members” setting). Show a role's unicode/custom text icon inline and image role icons beside the role mention when available; keep account and manually assigned bot badges.

**Why:** The user asked for server role icons to appear as badges automatically when a member has the role.

**How to apply:** Resolve the target against the command's guild, filter by the role's display-separately setting, use each live role's display icon when available, and do not persist a second copy of role membership in `badges.json`.
