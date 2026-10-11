import discord
import json
from discord.ext import commands
from discord import app_commands
from utils.emojis import e
from utils.Tools import blacklist_check, ignore_check


class Vanityroles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Slash command group ───────────────────────────────────────────────

    vr_group = app_commands.Group(
        name="vanityroles",
        description="Configure vanity role rewards for your server",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    @vr_group.command(name="setup", description="Set up vanity roles: keyword, reward role, and log channel")
    @app_commands.describe(
        keyword="The text members must put in their status (e.g. discord.gg/yourserver)",
        role="Role to give when a member adds the keyword",
        channel="Channel to log vanity status changes",
    )
    async def vr_setup(self, interaction: discord.Interaction,
                       keyword: str,
                       role: discord.Role,
                       channel: discord.TextChannel):
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} You need **Administrator** permission.", color=0x2f3136),
                ephemeral=True
            )
        if role.permissions.administrator or role.permissions.ban_members or role.permissions.kick_members:
            return await interaction.response.send_message(
                embed=discord.Embed(
            description=f"{e.cross_mark} Vanity role cannot have **Administrator**, **Ban** or **Kick** permissions.",
                    color=0x2f3136
                ),
                ephemeral=True
            )

        with open("vanityroles.json", "r") as f:
            data = json.load(f)

        data[str(interaction.guild.id)] = {
            "vanity": keyword,
            "role": role.id,
            "channel": channel.id
        }

        with open("vanityroles.json", "w") as f:
            json.dump(data, f, indent=4)

        embed = discord.Embed(title=f"{e.white_check} Vanity Roles Set Up", color=0x2f3136)
        embed.add_field(name=f"{e.dot_white} Keyword", value=f"`{keyword}`", inline=False)
        embed.add_field(name=f"{e.dot_white} Reward Role", value=role.mention, inline=False)
        embed.add_field(name=f"{e.dot_white} Log Channel", value=channel.mention, inline=False)
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @vr_group.command(name="remove", description="Remove the vanity roles setup for this server")
    async def vr_remove(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} You need **Administrator** permission.", color=0x2f3136),
                ephemeral=True
            )
        with open("vanityroles.json", "r") as f:
            data = json.load(f)

        if str(interaction.guild.id) not in data:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} No vanity roles are set up for this server.", color=0x2f3136),
                ephemeral=True
            )

        data.pop(str(interaction.guild.id))
        with open("vanityroles.json", "w") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.green_tick} | Vanity roles setup has been removed.", color=0x2f3136)
        )

    @vr_group.command(name="config", description="Show the current vanity roles config")
    async def vr_config(self, interaction: discord.Interaction):
        with open("vanityroles.json", "r") as f:
            data = json.load(f)

        if str(interaction.guild.id) not in data:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} No vanity roles configured. Use `/vanityroles setup` first.", color=0x2f3136),
                ephemeral=True
            )

        cfg = data[str(interaction.guild.id)]
        vanity = cfg.get("vanity", "Not Set")
        role = interaction.guild.get_role(cfg.get("role", 0))
        channel = interaction.guild.get_channel(cfg.get("channel", 0))

        embed = discord.Embed(title="Vanity Roles Config", color=0x2f3136)
        embed.set_author(name=str(interaction.guild), icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
        embed.add_field(name=f"{e.dot_white} Keyword", value=f"`{vanity}`", inline=False)
        embed.add_field(name=f"{e.dot_white} Reward Role", value=role.mention if role else "*(deleted)*", inline=False)
        embed.add_field(name=f"{e.dot_white} Log Channel", value=channel.mention if channel else "*(deleted)*", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Prefix fallback (vr setup / vr remove / vr config) ───────────────

    @commands.group(name="vr", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def vr_prefix(self, ctx):
        embed = discord.Embed(
            title="Vanity Roles",
            description=(
                "Use the slash commands instead:\n"
                "`/vanityroles setup` — configure vanity roles\n"
                "`/vanityroles remove` — remove the config\n"
                "`/vanityroles config` — view current config"
            ),
            color=0x2f3136
        )
        await ctx.send(embed=embed)

    # ── Presence listener ─────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        try:
            with open("vanityroles.json", "r") as f:
                jnl = json.load(f)

            guild_id = str(before.guild.id)
            if guild_id not in jnl:
                return

            cfg = jnl[guild_id]
            keyword = cfg["vanity"]
            grole = after.guild.get_role(cfg["role"])
            gchannel = after.guild.get_channel(cfg["channel"])

            if before.bot:
                return
            if str(before.status) == "offline":
                return

            # Build a searchable string from all activities
            activity_text = " ".join(
                str(a) for a in (after.activities or [])
            ).lower()

            has_keyword = keyword.lower() in activity_text
            has_role = grole in after.roles if grole else False

            if has_keyword and not has_role and grole:
                await after.add_roles(grole, reason=f"Vanity status: added '{keyword}'")
                if gchannel:
                    embed = discord.Embed(
            title=f"{e.glowing_star} New Vanity Status!",
                        description=(
                            f"{after.mention} added `{keyword}` to their status!\n"
            f"They've been given the {grole.mention} role. Thank you! {e.folded_hands}"
                        ),
                        color=0x2f3136
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    await gchannel.send(embed=embed)

            elif not has_keyword and has_role and grole:
                await after.remove_roles(grole, reason=f"Vanity status: removed '{keyword}'")
                if gchannel:
                    embed = discord.Embed(
                        title="Vanity Status Removed",
                        description=(
                            f"{after.mention} removed `{keyword}` from their status.\n"
                            f"The {grole.mention} role has been taken back."
                        ),
                        color=0x2f3136
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    await gchannel.send(embed=embed)
        except Exception:
            pass

async def setup(client):
    await client.add_cog(Vanityroles(client))
