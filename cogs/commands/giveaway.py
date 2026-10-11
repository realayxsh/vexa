import asyncio
import copy
import json
import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import discord
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

_DURATION_TOKEN = re.compile(r"(\d+)\s*([smhd])", re.IGNORECASE)
_MAX_DURATION_SECONDS = 365 * 24 * 60 * 60
_MAX_WINNERS = 20
_EMBED_COLOR = 0x2F3136
_STORE_PATH = Path("giveaways.json")


def parse_duration(value: str) -> int:
    """Parse a duration such as 30m, 2h, or 1d12h into seconds."""
    tokens = list(_DURATION_TOKEN.finditer(value))
    compact_value = re.sub(r"\s+", "", value)
    if not tokens or "".join(token.group(0).replace(" ", "") for token in tokens) != compact_value:
        raise ValueError("Use a duration such as `30m`, `2h`, or `1d12h`.")

    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    seconds = sum(
        int(token.group(1)) * units[token.group(2).lower()]
        for token in tokens
    )
    if seconds < 10:
        raise ValueError("A giveaway must last at least 10 seconds.")
    if seconds > _MAX_DURATION_SECONDS:
        raise ValueError("A giveaway cannot last more than 365 days.")
    return seconds


def _read_store(path: Path) -> dict:
    if not path.exists():
        return {"settings": {}, "giveaways": {}}
    with path.open("r", encoding="utf-8") as store_file:
        data = json.load(store_file)
    if not isinstance(data, dict):
        raise ValueError("giveaways.json must contain a JSON object.")
    data.setdefault("settings", {})
    data.setdefault("giveaways", {})
    if not isinstance(data["settings"], dict) or not isinstance(data["giveaways"], dict):
        raise ValueError("giveaways.json has an invalid settings or giveaways section.")
    return data


def _write_store(path: Path, data: dict) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as store_file:
        json.dump(data, store_file, indent=2, ensure_ascii=False)
        store_file.write("\n")
    temporary_path.replace(path)


class GiveawayEntryButton(discord.ui.Button):
    def __init__(self, cog: "Giveaways", giveaway_key: str, emoji: str):
        super().__init__(
            label="Enter / leave",
            style=discord.ButtonStyle.success,
            emoji=discord.PartialEmoji.from_str(emoji),
            custom_id=f"giveaway:entry:{giveaway_key}",
        )
        self.cog = cog
        self.giveaway_key = giveaway_key

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        if interaction.guild_id is None:
            return await interaction.followup.send(
                "Giveaways can only be entered from a server.", ephemeral=True
            )
        result = await self.cog._toggle_entry(
            self.giveaway_key, interaction.guild_id, interaction.user.id
        )
        if result is None:
            return await interaction.followup.send(
                "This giveaway is no longer open.", ephemeral=True
            )
        joined, count = result
        message = "You entered the giveaway." if joined else "You left the giveaway."
        await interaction.followup.send(f"{message} Entries: **{count}**.", ephemeral=True)


class GiveawayEntryView(discord.ui.View):
    def __init__(self, cog: "Giveaways", giveaway_key: str, emoji: str):
        super().__init__(timeout=None)
        self.add_item(GiveawayEntryButton(cog, giveaway_key, emoji))


class Giveaways(commands.Cog):
    """Persistent giveaways, with per-server button or reaction entry."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store_path = _STORE_PATH
        self._store_lock = asyncio.Lock()
        self._action_lock = asyncio.Lock()

    async def cog_load(self) -> None:
        await self._mutate(self._recover_interrupted_finishes)
        data = await self._read()
        for key, giveaway in data["giveaways"].items():
            if giveaway.get("status") == "active" and giveaway.get("mode") == "button":
                self.bot.add_view(
                    GiveawayEntryView(self, key, giveaway["emoji"]),
                    message_id=int(giveaway["message_id"]),
                )
        self._expiry_loop.start()

    def cog_unload(self) -> None:
        self._expiry_loop.cancel()

    @staticmethod
    def _recover_interrupted_finishes(data: dict) -> None:
        for giveaway in data["giveaways"].values():
            if giveaway.get("status") == "ending":
                giveaway["status"] = "active"

    async def _read(self) -> dict:
        async with self._store_lock:
            return copy.deepcopy(await asyncio.to_thread(_read_store, self.store_path))

    async def _mutate(self, callback):
        async with self._store_lock:
            data = await asyncio.to_thread(_read_store, self.store_path)
            result = callback(data)
            await asyncio.to_thread(_write_store, self.store_path, data)
            return result

    async def _settings(self, guild_id: int) -> dict:
        data = await self._read()
        return data["settings"].get(
            str(guild_id), {"mode": "button", "emoji": None}
        )

    @staticmethod
    def _make_embed(giveaway: dict) -> discord.Embed:
        status = giveaway["status"]
        ends_at = int(giveaway["ends_at"])
        entries = len(giveaway.get("entries", []))
        embed = discord.Embed(
            title=f"🎉 Giveaway — {giveaway['prize']}",
            color=_EMBED_COLOR,
        )
        embed.add_field(name="Hosted by", value=f"<@{giveaway['host_id']}>", inline=True)
        embed.add_field(name="Winners", value=str(giveaway["winner_count"]), inline=True)
        embed.add_field(name="Entries", value=str(entries), inline=True)

        if status == "active":
            if giveaway["mode"] == "button":
                entry_text = f"Press the {giveaway['emoji']} button below to enter or leave."
            else:
                entry_text = f"React with {giveaway['emoji']} to enter or remove your reaction to leave."
            embed.description = (
                f"{entry_text}\nEnds <t:{ends_at}:R> "
                f"(<t:{ends_at}:f>)."
            )
        elif status == "cancelled":
            embed.description = "This giveaway was cancelled."
        else:
            winners = giveaway.get("winners", [])
            winner_text = ", ".join(f"<@{user_id}>" for user_id in winners)
            embed.description = (
                f"Giveaway ended with **{entries}** entr{'y' if entries == 1 else 'ies'}."
            )
            embed.add_field(
                name="Winner" if len(winners) == 1 else "Winners",
                value=winner_text or "No eligible entries.",
                inline=False,
            )
        embed.set_footer(text=f"Giveaway ID: {giveaway['message_id']}")
        return embed

    @staticmethod
    def _valid_store_entry(
        data: dict, giveaway_key: str, guild_id: int
    ) -> Optional[dict]:
        giveaway = data["giveaways"].get(giveaway_key)
        if not giveaway or int(giveaway["guild_id"]) != guild_id:
            return None
        return giveaway

    async def _toggle_entry(
        self, giveaway_key: str, guild_id: int, user_id: int
    ) -> Optional[tuple[bool, int]]:
        def toggle(data: dict):
            giveaway = self._valid_store_entry(data, giveaway_key, guild_id)
            if not giveaway or giveaway.get("status") != "active":
                return None
            entries = list(dict.fromkeys(int(value) for value in giveaway.get("entries", [])))
            if user_id in entries:
                entries.remove(user_id)
                joined = False
            else:
                entries.append(user_id)
                joined = True
            giveaway["entries"] = entries
            return joined, len(entries)

        return await self._mutate(toggle)

    @staticmethod
    def _can_manage(ctx: commands.Context, giveaway: dict) -> bool:
        permissions = getattr(ctx.author, "guild_permissions", None)
        return (
            ctx.author.id == int(giveaway["host_id"])
            or bool(permissions and permissions.manage_guild)
        )

    async def _find_giveaway(self, guild_id: int, message_id: int):
        data = await self._read()
        for key, giveaway in data["giveaways"].items():
            if (int(giveaway["guild_id"]) == guild_id
                    and int(giveaway.get("message_id", 0)) == message_id):
                return key, giveaway
        return None, None

    async def _fetch_message(self, giveaway: dict):
        channel_id = int(giveaway["channel_id"])
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)
        return await channel.fetch_message(int(giveaway["message_id"])), channel

    @staticmethod
    async def _send(ctx: commands.Context, content=None, *, ephemeral=False, **kwargs):
        if ctx.interaction is not None:
            kwargs["ephemeral"] = ephemeral
        return await ctx.send(content, **kwargs)

    def help_custom(self):
        return "🎁", "Giveaways", "Create, join, and manage server giveaways."

    @commands.hybrid_group(
        name="giveaway",
        invoke_without_command=True,
        description="Create and manage server giveaways.",
        help="Create, configure, join, end, cancel, reroll, and list server giveaways.",
    )
    @commands.guild_only()
    async def giveaway(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @giveaway.command(
        name="start",
        description="Start a giveaway in this channel.",
        help="Usage: `/giveaway start prize duration winners`. Duration examples: `30m`, `2h`, `1d`.",
    )
    @app_commands.describe(
        prize="The giveaway prize",
        duration="How long it runs, for example 30m, 2h, or 1d12h",
        winners="Number of winners (1–20)",
    )
    async def giveaway_start(
        self,
        ctx: commands.Context,
        prize: str,
        duration: str,
        winners: int = 1,
    ) -> None:
        if not ctx.author.guild_permissions.manage_guild:
            return await self._send(
                ctx, "You need **Manage Server** permission to start a giveaway.",
                ephemeral=True,
            )
        prize = prize.strip()
        if not prize or len(prize) > 180:
            return await self._send(ctx, "Prize must be between 1 and 180 characters.", ephemeral=True)
        if not 1 <= winners <= _MAX_WINNERS:
            return await self._send(ctx, f"Choose between 1 and {_MAX_WINNERS} winners.", ephemeral=True)
        try:
            duration_seconds = parse_duration(duration)
        except ValueError as error:
            return await self._send(ctx, str(error), ephemeral=True)

        settings = await self._settings(ctx.guild.id)
        emoji = settings.get("emoji")
        mode = settings.get("mode", "button")
        if not emoji:
            return await self._send(
                ctx,
                "A server administrator must set the entry emoji first with "
                "`/giveaway emoji <custom emoji>`.",
                ephemeral=True,
            )

        bot_member = ctx.guild.me
        permissions = ctx.channel.permissions_for(bot_member)
        if not permissions.send_messages or not permissions.embed_links:
            return await self._send(
                ctx, "I need **Send Messages** and **Embed Links** in this channel.",
                ephemeral=True,
            )
        if mode == "reaction" and not permissions.add_reactions:
            return await self._send(
                ctx, "I need **Add Reactions** permission in this channel for reaction entry.",
                ephemeral=True,
            )

        now = int(datetime.now(timezone.utc).timestamp())
        key = uuid4().hex
        giveaway = {
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "message_id": 0,
            "host_id": ctx.author.id,
            "prize": prize,
            "winner_count": winners,
            "ends_at": now + duration_seconds,
            "entries": [],
            "mode": mode,
            "emoji": emoji,
            "status": "active",
            "winners": [],
            "winner_history": [],
        }
        view = GiveawayEntryView(self, key, emoji) if mode == "button" else None
        message = await ctx.send(embed=self._make_embed(giveaway), view=view)
        giveaway["message_id"] = message.id
        try:
            if mode == "reaction":
                await message.add_reaction(discord.PartialEmoji.from_str(emoji))

            def save(data: dict):
                data["giveaways"][key] = giveaway

            await self._mutate(save)
        except Exception:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            raise

        await self._send(
            ctx,
            f"Giveaway started in {ctx.channel.mention}. ID: `{message.id}`",
            ephemeral=True,
        )

    @giveaway.command(name="emoji", description="Set the server's custom giveaway entry emoji.")
    @app_commands.describe(emoji="Paste a custom emoji from this server")
    async def giveaway_emoji(self, ctx: commands.Context, emoji: str) -> None:
        if not ctx.author.guild_permissions.administrator:
            return await self._send(ctx, "Only a server administrator can set this.", ephemeral=True)
        parsed = discord.PartialEmoji.from_str(emoji.strip())
        server_emoji = ctx.guild.get_emoji(parsed.id) if parsed.id else None
        if server_emoji is None:
            return await self._send(
                ctx,
                "Use a custom emoji from this server. Copy and paste it here, "
                "for example `<:name:123456789012345678>`.",
                ephemeral=True,
            )

        stored_emoji = str(server_emoji)

        def update(data: dict):
            settings = data["settings"].setdefault(
                str(ctx.guild.id), {"mode": "button", "emoji": None}
            )
            settings["emoji"] = stored_emoji

        await self._mutate(update)
        await self._send(
            ctx,
            f"Giveaway entry emoji set to {stored_emoji}. This applies to new giveaways.",
            ephemeral=True,
        )

    @giveaway.command(name="mode", description="Choose button or reaction giveaway entry.")
    @app_commands.describe(mode="Choose button or reaction")
    async def giveaway_mode(self, ctx: commands.Context, mode: str) -> None:
        if not ctx.author.guild_permissions.administrator:
            return await self._send(ctx, "Only a server administrator can set this.", ephemeral=True)
        mode = mode.strip().lower()
        if mode not in {"button", "reaction"}:
            return await self._send(ctx, "Choose `button` or `reaction`.", ephemeral=True)

        def update(data: dict):
            settings = data["settings"].setdefault(
                str(ctx.guild.id), {"mode": "button", "emoji": None}
            )
            settings["mode"] = mode

        await self._mutate(update)
        await self._send(
            ctx,
            f"New giveaways will use **{mode}** entry. Existing giveaways are unchanged.",
            ephemeral=True,
        )

    @giveaway.command(name="config", description="Show giveaway settings for this server.")
    async def giveaway_config(self, ctx: commands.Context) -> None:
        settings = await self._settings(ctx.guild.id)
        embed = discord.Embed(title="Giveaway Settings", color=_EMBED_COLOR)
        embed.add_field(name="Entry method", value=settings.get("mode", "button").title())
        embed.add_field(name="Entry emoji", value=settings.get("emoji") or "Not set")
        embed.set_footer(text="Server administrators can change these settings.")
        await self._send(ctx, embed=embed, ephemeral=True)

    @giveaway.command(name="list", description="List active giveaways in this server.")
    async def giveaway_list(self, ctx: commands.Context) -> None:
        data = await self._read()
        active = [
            giveaway for giveaway in data["giveaways"].values()
            if int(giveaway["guild_id"]) == ctx.guild.id
            and giveaway.get("status") == "active"
        ]
        active.sort(key=lambda item: int(item["ends_at"]))
        embed = discord.Embed(title="Active Giveaways", color=_EMBED_COLOR)
        if not active:
            embed.description = "There are no active giveaways in this server."
        else:
            for giveaway in active[:10]:
                embed.add_field(
                    name=f"{giveaway['prize']} — ID `{giveaway['message_id']}`",
                    value=(
                        f"Channel: <#{giveaway['channel_id']}> • "
                        f"Ends <t:{giveaway['ends_at']}:R> • "
                        f"{len(giveaway.get('entries', []))} entries"
                    ),
                    inline=False,
                )
            if len(active) > 10:
                embed.set_footer(text=f"Showing 10 of {len(active)} active giveaways.")
        await self._send(ctx, embed=embed)

    async def _authorize_giveaway(
        self, ctx: commands.Context, message_id: int
    ):
        key, giveaway = await self._find_giveaway(ctx.guild.id, message_id)
        if giveaway is None:
            await self._send(ctx, "I couldn't find that giveaway in this server.", ephemeral=True)
            return None, None
        if not self._can_manage(ctx, giveaway):
            await self._send(
                ctx, "Only the giveaway host or a member with **Manage Server** can do that.",
                ephemeral=True,
            )
            return None, None
        return key, giveaway

    @giveaway.command(name="end", description="End an active giveaway early and select winners.")
    async def giveaway_end(self, ctx: commands.Context, message_id: str) -> None:
        if not message_id.isdigit():
            return await self._send(ctx, "Enter the numeric message ID shown by the giveaway.", ephemeral=True)
        key, giveaway = await self._authorize_giveaway(ctx, int(message_id))
        if key is None:
            return
        result = await self._finish(key, force=True)
        await self._send(ctx, result, ephemeral=True)

    @giveaway.command(name="cancel", description="Cancel an active giveaway without choosing winners.")
    async def giveaway_cancel(self, ctx: commands.Context, message_id: str) -> None:
        if not message_id.isdigit():
            return await self._send(ctx, "Enter the numeric message ID shown by the giveaway.", ephemeral=True)
        key, giveaway = await self._authorize_giveaway(ctx, int(message_id))
        if key is None:
            return
        async with self._action_lock:
            current = (await self._read())["giveaways"].get(key)
            if not current or current.get("status") != "active":
                return await self._send(ctx, "That giveaway is not active.", ephemeral=True)
            cancelled = dict(current, status="cancelled")
            try:
                message, _ = await self._fetch_message(current)
                await message.edit(embed=self._make_embed(cancelled), view=None)
            except discord.NotFound:
                pass
            except discord.HTTPException:
                return await self._send(ctx, "I couldn't update the giveaway message.", ephemeral=True)

            def cancel(data: dict):
                record = data["giveaways"].get(key)
                if record and record.get("status") == "active":
                    record["status"] = "cancelled"

            await self._mutate(cancel)
        await self._send(ctx, "Giveaway cancelled.", ephemeral=True)

    async def _announce_winners(self, giveaway: dict, winners: list[int], channel) -> None:
        if not winners:
            return
        mentions = ", ".join(f"<@{user_id}>" for user_id in winners)
        try:
            await channel.send(
                f"🎉 Congratulations {mentions}! You won **{giveaway['prize']}**.",
                allowed_mentions=discord.AllowedMentions(
                    users=[discord.Object(id=user_id) for user_id in winners],
                    everyone=False,
                    roles=False,
                ),
            )
        except discord.HTTPException:
            logger.exception("Could not announce giveaway winners for message %s",
                             giveaway["message_id"])

    async def _finish(self, key: str, *, force: bool = False) -> str:
        async with self._action_lock:
            data = await self._read()
            giveaway = data["giveaways"].get(key)
            if not giveaway or giveaway.get("status") != "active":
                return "That giveaway is not active."
            if not force and int(giveaway["ends_at"]) > int(datetime.now(timezone.utc).timestamp()):
                return "That giveaway has not ended yet."

            def mark_ending(store: dict):
                record = store["giveaways"].get(key)
                if record and record.get("status") == "active":
                    record["status"] = "ending"

            await self._mutate(mark_ending)
            giveaway = dict(giveaway)
            giveaway["status"] = "ended"
            entrants = list(dict.fromkeys(int(value) for value in giveaway.get("entries", [])))
            winners = random.sample(entrants, min(int(giveaway["winner_count"]), len(entrants)))
            giveaway["winners"] = winners
            giveaway["winner_history"] = winners[:]

            try:
                message, channel = await self._fetch_message(giveaway)
                await message.edit(embed=self._make_embed(giveaway), view=None)
            except discord.NotFound:
                def close_missing(store: dict):
                    record = store["giveaways"].get(key)
                    if record:
                        record["status"] = "cancelled"
                await self._mutate(close_missing)
                return "The giveaway message was deleted, so I closed the giveaway."
            except discord.HTTPException:
                def reopen(store: dict):
                    record = store["giveaways"].get(key)
                    if record and record.get("status") == "ending":
                        record["status"] = "active"
                await self._mutate(reopen)
                logger.exception("Could not finish giveaway %s", key)
                return "I couldn't update the giveaway message. It remains active; please try again."

            def finish(store: dict):
                record = store["giveaways"].get(key)
                if record:
                    record["status"] = "ended"
                    record["winners"] = winners
                    record["winner_history"] = winners[:]
                    record["ended_at"] = int(datetime.now(timezone.utc).timestamp())

            await self._mutate(finish)
            await self._announce_winners(giveaway, winners, channel)
            if not winners:
                return "Giveaway ended. There were no entries to draw from."
            return "Giveaway ended and the winners were announced."

    @giveaway.command(name="reroll", description="Choose a new winner from the remaining entrants.")
    async def giveaway_reroll(self, ctx: commands.Context, message_id: str) -> None:
        if not message_id.isdigit():
            return await self._send(ctx, "Enter the numeric message ID shown by the giveaway.", ephemeral=True)
        key, giveaway = await self._authorize_giveaway(ctx, int(message_id))
        if key is None:
            return
        async with self._action_lock:
            current = (await self._read())["giveaways"].get(key)
            if not current or current.get("status") != "ended":
                return await self._send(ctx, "Only an ended giveaway can be rerolled.", ephemeral=True)
            entries = list(dict.fromkeys(int(value) for value in current.get("entries", [])))
            history = set(int(value) for value in current.get("winner_history", []))
            remaining = [user_id for user_id in entries if user_id not in history]
            if not remaining:
                return await self._send(ctx, "There are no non-winning entrants left to reroll.", ephemeral=True)
            new_winners = random.sample(
                remaining, min(int(current["winner_count"]), len(remaining))
            )
            rerolled = dict(current, winners=new_winners)
            rerolled["winner_history"] = list(history.union(new_winners))
            try:
                message, channel = await self._fetch_message(current)
                await message.edit(embed=self._make_embed(rerolled), view=None)
            except discord.HTTPException:
                return await self._send(ctx, "I couldn't update the giveaway message.", ephemeral=True)

            def update(data: dict):
                record = data["giveaways"].get(key)
                if record:
                    record["winners"] = new_winners
                    record["winner_history"] = sorted(
                        set(int(value) for value in record.get("winner_history", []))
                        | set(new_winners)
                    )

            await self._mutate(update)
            await self._announce_winners(rerolled, new_winners, channel)
        await self._send(ctx, "The giveaway was rerolled.", ephemeral=True)

    @tasks.loop(seconds=20)
    async def _expiry_loop(self) -> None:
        data = await self._read()
        now = int(datetime.now(timezone.utc).timestamp())
        for key, giveaway in data["giveaways"].items():
            if giveaway.get("status") == "active" and int(giveaway["ends_at"]) <= now:
                result = await self._finish(key)
                if result.startswith("I couldn't"):
                    logger.warning("Giveaway %s is overdue: %s", key, result)

    @_expiry_loop.before_loop
    async def _before_expiry_loop(self) -> None:
        await self.bot.wait_until_ready()

    async def _handle_reaction(self, payload: discord.RawReactionActionEvent, joined: bool) -> None:
        if payload.guild_id is None or self.bot.user is None:
            return
        if payload.user_id == self.bot.user.id:
            return
        data = await self._read()
        match = next(
            (
                (key, giveaway)
                for key, giveaway in data["giveaways"].items()
                if int(giveaway.get("message_id", 0)) == payload.message_id
            ),
            (None, None),
        )
        key, giveaway = match
        if (
            giveaway is None
            or giveaway.get("status") != "active"
            or giveaway.get("mode") != "reaction"
            or int(giveaway["guild_id"]) != payload.guild_id
            or str(payload.emoji) != giveaway.get("emoji")
        ):
            return

        def update(store: dict):
            record = self._valid_store_entry(store, key, payload.guild_id)
            if not record or record.get("status") != "active":
                return
            entries = list(dict.fromkeys(int(value) for value in record.get("entries", [])))
            if joined and payload.user_id not in entries:
                entries.append(payload.user_id)
            elif not joined and payload.user_id in entries:
                entries.remove(payload.user_id)
            record["entries"] = entries

        await self._mutate(update)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self._handle_reaction(payload, joined=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self._handle_reaction(payload, joined=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Giveaways(bot))
