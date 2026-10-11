
# ============================================================
#  Yawr Support  —  Permission System
#
#  Role hierarchy (highest → lowest):
#    Server Owner  →  everything
#    Co Owner role →  ban, kick, mute, warn + all role commands
#    Admin role    →  give / remove server roles only
#    Everyone else →  BLOCKED
# ============================================================

import discord
from discord.ext import commands
from utils.Tools import getConfig


# ── Custom exceptions (shown to users) ──────────────────────

class NotServerOwner(commands.CheckFailure):
    pass

class NotCoOwnerOrAbove(commands.CheckFailure):
    pass

class NotAdminOrAbove(commands.CheckFailure):
    pass

class RoleNotConfigured(commands.CheckFailure):
    def __init__(self, role_type: str):
        self.role_type = role_type
        super().__init__(f"The `{role_type}` role has not been set up yet.")


# ── Helper ───────────────────────────────────────────────────

def _get_role_id(guild_id: int, key: str):
    """Return the configured role ID or None."""
    data = getConfig(guild_id)
    return data.get(key)


def _member_has_role(member: discord.Member, role_id) -> bool:
    if not role_id:
        return False
    return any(r.id == int(role_id) for r in member.roles)


def _is_server_owner(ctx) -> bool:
    if not ctx.guild:
        return False
    return ctx.author.id == ctx.guild.owner_id


def _is_coowner_or_above(ctx) -> bool:
    if _is_server_owner(ctx):
        return True
    coown_id = _get_role_id(ctx.guild.id, "coown")
    return _member_has_role(ctx.author, coown_id)


def _is_admin_or_above(ctx) -> bool:
    if _is_coowner_or_above(ctx):
        return True
    admin_id = _get_role_id(ctx.guild.id, "admin")
    return _member_has_role(ctx.author, admin_id)


# ── Public check decorators ──────────────────────────────────

def server_owner_check():
    """Only the Discord server owner may use this command."""
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if not _is_server_owner(ctx):
            raise NotServerOwner(
                "Only the **server owner** can use this command.")
        return True
    return commands.check(predicate)


def coowner_check():
    """Server owner OR a member with the configured Co Owner role."""
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if _is_coowner_or_above(ctx):
            return True
        raise NotCoOwnerOrAbove(
            "You need the **Co Owner** role (or be the server owner) "
            "to use this command.")
    return commands.check(predicate)


def admin_check():
    """Server owner, Co Owner, OR a member with the configured Admin role."""
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if _is_admin_or_above(ctx):
            return True
        raise NotAdminOrAbove(
            "You need the **Admin** role (or higher) to use this command.")
    return commands.check(predicate)


# ── Global bot-level check (registered in core/Dilbar.py) ───

async def global_permission_check(ctx) -> bool:
    """
    Runs before every command.
    Blocks everyone except server owner, co-owners and admins.
    Bot owners bypass all checks.
    DM commands are blocked entirely.
    """
    # Always allow bot owners
    if ctx.author.id in ctx.bot.owner_ids:
        return True

    # Block DMs (this is a server-only bot)
    if not ctx.guild:
        return False

    # Help describes commands; it does not grant permission to run them.
    if ctx.command is not None and ctx.command.qualified_name == "help":
        return True

    # Server owner → full access
    if _is_server_owner(ctx):
        return True

    # Co Owner role → full access
    coown_id = _get_role_id(ctx.guild.id, "coown")
    if _member_has_role(ctx.author, coown_id):
        return True

    # Admin role → limited access (role commands only)
    admin_id = _get_role_id(ctx.guild.id, "admin")
    if _member_has_role(ctx.author, admin_id):
        return True

    # Everyone else → blocked silently
    return False
