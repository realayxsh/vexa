---
name: Role-derived badges
description: How server roles and their icons appear in the bot's badges command.
---

The `/badges` command should include only the target member's current-server roles with `role.hoist` enabled (Discord's “Display role members separately from online members” setting). Include the target member's display name in the heading. Show unicode/custom text icons inline; for image role icons, match the image against the server's custom emoji images and show a matching emoji inline. If no image match is available, show the role mention without an icon. Do not show account or manually assigned bot badges.

**Why:** The user asked for server role icons to appear as badges automatically when a member has the role.

**How to apply:** Resolve the target against the command's guild, filter by the role's display-separately setting, use each live role's display icon when available, and do not persist a second copy of role membership in `badges.json`.
