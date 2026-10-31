import discord
import asyncio
from discord.ext import commands, tasks
from utils.Tools import getDB, updateDB, blacklist_check, ignore_check
from utils.emojis import e
from utils.permissions import server_owner_check
from core import Cog, Dilbar, Context


class Stay(Cog):
    """24/7 voice channel — bot sits silently in VC and auto-reconnects."""

    def __init__(self, bot: Dilbar):
        self.bot = bot
        self._reconnect_loop.start()

    def cog_unload(self):
        self._reconnect_loop.cancel()

    # ── helpers ──────────────────────────────────────────────────────────

    def _get_stay_channel(self, guild_id: int):
        """Return stored 24/7 VC channel ID or None."""
        data = getDB(guild_id)
        return data.get("stay_vc")

    def _set_stay_channel(self, guild_id: int, channel_id):
        data = getDB(guild_id)
        data["stay_vc"] = channel_id
        updateDB(guild_id, data)

    # ── background task: reconnect every 30s if dropped ─────────────────

    @tasks.loop(seconds=30)
    async def _reconnect_loop(self):
        for guild in self.bot.guilds:
            ch_id = self._get_stay_channel(guild.id)
            if not ch_id:
                continue

            channel = guild.get_channel(int(ch_id))
            if channel is None:
                continue

            vc = guild.voice_client

            # Already connected to the right channel — nothing to do
            if vc and vc.is_connected() and vc.channel.id == channel.id:
                continue

            # Connected somewhere else — move to the correct channel
            if vc and vc.is_connected():
                try:
                    await vc.move_to(channel)
                except Exception:
                    pass
                continue

            # Not connected at all — join
            try:
                await channel.connect(self_deaf=True, self_mute=True)
            except Exception:
                pass

    @_reconnect_loop.before_loop
    async def _before_reconnect(self):
        await self.bot.wait_until_ready()

    # ── commands ─────────────────────────────────────────────────────────

    @commands.group(
        name="stay",
        aliases=["247", "24/7"],
        invoke_without_command=True,
        help="24/7 voice channel management.",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @server_owner_check()
    async def _stay(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @_stay.command(
        name="join",
        aliases=["set", "start"],
        help="Make the bot join and stay in a voice channel 24/7.",
        usage="stay join <#channel>",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @server_owner_check()
    async def stay_join(self, ctx: Context, channel: discord.VoiceChannel):
        self._set_stay_channel(ctx.guild.id, channel.id)

        # Connect now (disconnect from old channel first if needed)
        vc = ctx.guild.voice_client
        try:
            if vc and vc.is_connected():
                await vc.move_to(channel)
            else:
                await channel.connect(self_deaf=True, self_mute=True)
        except Exception as err:
            embed = discord.Embed(
                description=f"{e.red_cross} | Could not join **{channel.name}**: `{err}`",
                color=0x2f3136,
            )
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            return await ctx.reply(embed=embed, mention_author=False)

        embed = discord.Embed(
            description=(
                f"{e.green_tick} | Joined **{channel.name}** and will stay there **24/7**.\n"
                f"The bot auto-reconnects if it gets disconnected.\n"
                f"Use `stay leave` to stop."
            ),
            color=0x2f3136,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @_stay.command(
        name="leave",
        aliases=["stop", "disconnect"],
        help="Make the bot leave the 24/7 voice channel.",
        usage="stay leave",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @server_owner_check()
    async def stay_leave(self, ctx: Context):
        ch_id = self._get_stay_channel(ctx.guild.id)

        # Clear the stored channel first so reconnect loop won't re-join
        self._set_stay_channel(ctx.guild.id, None)

        vc = ctx.guild.voice_client
        if vc and vc.is_connected():
            ch_name = vc.channel.name
            await vc.disconnect(force=True)
            embed = discord.Embed(
                description=f"{e.green_tick} | Left **{ch_name}** and disabled 24/7 mode.",
                color=0x2f3136,
            )
        else:
            embed = discord.Embed(
                description=f"{e.green_tick} | 24/7 mode disabled. Bot is not in any voice channel.",
                color=0x2f3136,
            )

        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @_stay.command(
        name="status",
        aliases=["info", "check"],
        help="Check the current 24/7 voice channel status.",
        usage="stay status",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @server_owner_check()
    async def stay_status(self, ctx: Context):
        ch_id = self._get_stay_channel(ctx.guild.id)
        vc    = ctx.guild.voice_client

        embed = discord.Embed(title="24/7 Voice Status", color=0x2f3136)

        if ch_id:
            ch = ctx.guild.get_channel(int(ch_id))
            embed.add_field(
                name="Configured Channel",
                value=ch.mention if ch else f"`{ch_id}` *(deleted)*",
                inline=True,
            )
        else:
            embed.add_field(name="Configured Channel", value="*(not set)*", inline=True)

        if vc and vc.is_connected():
            embed.add_field(name="Currently In", value=vc.channel.mention, inline=True)
            embed.add_field(name="Status", value=f"{e.green_circle} Connected", inline=True)
        else:
            embed.add_field(name="Currently In", value="*(not connected)*", inline=True)
            embed.add_field(name="Status", value=f"{e.red_circle} Disconnected", inline=True)

        embed.set_footer(text="Auto-reconnects every 30 seconds if dropped")
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    # ── event: reconnect immediately if bot is force-disconnected ────────

    @Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.id != self.bot.user.id:
            return

        # Bot was disconnected from a channel
        if before.channel and not after.channel:
            guild   = before.channel.guild
            ch_id   = self._get_stay_channel(guild.id)
            if not ch_id:
                return

            # Wait a moment before reconnecting (avoids tight loop on kick)
            await asyncio.sleep(3)

            channel = guild.get_channel(int(ch_id))
            if channel is None:
                return

            vc = guild.voice_client
            if vc and vc.is_connected():
                return  # Already reconnected somehow

            try:
                await channel.connect(self_deaf=True, self_mute=True)
            except Exception:
                pass
