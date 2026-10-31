
import discord
from discord.ext import commands
from utils.Tools import getConfig, updateConfig, blacklist_check, ignore_check
from utils.emojis import e
from utils.permissions import server_owner_check, NotServerOwner
from core import Cog, Dilbar, Context


class Setup(Cog):
    """Server owner commands to configure QTs Support role permissions."""

    def __init__(self, client: Dilbar):
        self.client = client

    # ── helpers ──────────────────────────────────────────────────────────

    def _save_role(self, guild_id: int, key: str, role_id):
        data = getConfig(guild_id)
        data[key] = role_id
        updateConfig(guild_id, data)

    def _role_display(self, guild: discord.Guild, role_id):
        if not role_id:
            return "*(not set)*"
        role = guild.get_role(int(role_id))
        return role.mention if role else f"*(deleted role — id {role_id})*"

    # ── set commands ─────────────────────────────────────────────────────

    @commands.command(
        name="setcoowner",
        aliases=["setco", "setcoown"],
        help="Set the Co Owner role. Co Owners can ban, kick, mute and use all mod commands.",
        usage="setcoowner <@role>",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def set_coowner(self, ctx: Context, role: discord.Role):
        self._save_role(ctx.guild.id, "coown", role.id)
        embed = discord.Embed(
            description=f"{e.green_tick} | **Co Owner** role set to {role.mention}\n"
                        f"Members with this role can now use **ban, kick, mute, warn** and all moderation commands.",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="setadmin",
        aliases=["setadm"],
        help="Set the Admin role. Admins can give and remove server roles from members.",
        usage="setadmin <@role>",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def set_admin(self, ctx: Context, role: discord.Role):
        self._save_role(ctx.guild.id, "admin", role.id)
        embed = discord.Embed(
            description=f"{e.green_tick} | **Admin** role set to {role.mention}\n"
                        f"Members with this role can now use all **role management** commands.",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="setmod",
        aliases=["setmoderator"],
        help="Set the Mod role for reference in the server.",
        usage="setmod <@role>",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def set_mod(self, ctx: Context, role: discord.Role):
        self._save_role(ctx.guild.id, "mod", role.id)
        embed = discord.Embed(
            description=f"{e.green_tick} | **Mod** role set to {role.mention}",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    # ── reset commands ───────────────────────────────────────────────────

    @commands.command(
        name="removecoowner",
        aliases=["delcoowner", "resetcoown"],
        help="Remove the configured Co Owner role.",
        usage="removecoowner",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def remove_coowner(self, ctx: Context):
        self._save_role(ctx.guild.id, "coown", None)
        embed = discord.Embed(
            description=f"{e.red_cross} | **Co Owner** role has been removed. Nobody except you can use moderation commands now.",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="removeadmin",
        aliases=["deladmin", "resetadmin"],
        help="Remove the configured Admin role.",
        usage="removeadmin",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def remove_admin(self, ctx: Context):
        self._save_role(ctx.guild.id, "admin", None)
        embed = discord.Embed(
            description=f"{e.red_cross} | **Admin** role has been removed. Nobody except you and Co Owners can use role commands now.",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    # ── Log channel setup commands ────────────────────────────────────────

    @commands.command(
        name="setbotlog",
        aliases=["setbotlogchannel"],
        description="Set the channel for bot command logs.",
        usage="setbotlog <#channel>",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def set_botlog(self, ctx: Context, channel: discord.TextChannel):
        data = getConfig(ctx.guild.id)
        data["botlog"] = channel.id
        updateConfig(ctx.guild.id, data)
        embed = discord.Embed(
            description=f"{e.green_tick} | **Bot log** channel set to {channel.mention}\n"
                        f"All bot command activity will now be logged there.",
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="logchannels",
        aliases=["logconfig", "logsettings"],
        description="Show all configured log channels for this server.",
        usage="logchannels",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def log_channels_status(self, ctx: Context):
        data = getConfig(ctx.guild.id)

        def _ch(cid):
            if not cid:
                return "*(not set)*"
            ch = ctx.guild.get_channel(int(cid))
            return ch.mention if ch else f"*(deleted — id {cid})*"

        embed = discord.Embed(title="Log Channel Config", color=0x2f3136)
        embed.add_field(name=f"{e.clipboard} Bot Log", value=_ch(data.get("botlog")), inline=False)
        embed.set_footer(text="Use setbotlog to configure")
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    # ── status command ───────────────────────────────────────────────────

    @commands.command(
        name="permissions",
        aliases=["perms", "rolesconfig", "botperms"],
        help="Shows the current permission role configuration for this server.",
        usage="permissions",
    )
    @blacklist_check()
    @ignore_check()
    @server_owner_check()
    async def permissions_status(self, ctx: Context):
        data = getConfig(ctx.guild.id)

        co_owner  = self._role_display(ctx.guild, data.get("coown"))
        admin     = self._role_display(ctx.guild, data.get("admin"))
        mod       = self._role_display(ctx.guild, data.get("mod"))
        staff     = self._role_display(ctx.guild, data.get("staff"))
        owner_r   = self._role_display(ctx.guild, data.get("owner"))

        embed = discord.Embed(
            title="QTs Support  —  Permission Config",
            color=0x2f3136,
        )
        embed.add_field(
            name=f"{e.king} Server Owner",
            value="The Discord server owner — full access to all commands.",
            inline=False,
        )
        embed.add_field(
            name=f"{e.crown} Co Owner Role",
            value=f"{co_owner}\n*Can use: ban, kick, mute, warn, lock, all mod commands + role commands*",
            inline=False,
        )
        embed.add_field(
            name=f"{e.moderation} Admin Role",
            value=f"{admin}\n*Can use: give/remove server roles*",
            inline=False,
        )
        embed.add_field(
            name=f"{e.staff_badge} Mod Role",
            value=f"{mod}\n*Informational only — set via `setmod`*",
            inline=False,
        )
        embed.add_field(
            name=f"{e.role} Owner Role  (given to members)",
            value=f"{owner_r}",
            inline=True,
        )
        embed.add_field(
            name=f"{e.role} Staff Role",
            value=f"{staff}",
            inline=True,
        )
        embed.set_footer(
            text="Use setcoowner / setadmin to configure • Only server owner can run these"
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


