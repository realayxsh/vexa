import discord
from discord.ext import commands
from core import Cog, Dilbar, Context
from utils.Tools import *
from typing import *


def _apply_vars(text: str, member: discord.Member) -> str:
    """Replace <<placeholder>> tokens with live values."""
    replacements = {
        "<<server.name>>":         member.guild.name,
        "<<server.member_count>>": str(member.guild.member_count),
        "<<user.name>>":           str(member),
        "<<user.mention>>":        member.mention,
        "<<user.created_at>>":     f"<t:{int(member.created_at.timestamp())}:F>",
        "<<user.joined_at>>":      f"<t:{int(member.joined_at.timestamp())}:F>",
    }
    for token, value in replacements.items():
        if token in text:
            text = text.replace(token, value)
    return text


class greet(Cog):
    def __init__(self, bot: Dilbar):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data      = getDB(member.guild.id)
        wdata     = data["welcome"]
        channels  = list(wdata.get("channel", []))

        if not channels:
            return

        # ── read settings ─────────────────────────────────────────
        emtog       = wdata.get("embed", False)
        emping      = wdata.get("ping", False)
        emimage     = wdata.get("image", "")
        emthumbnail = wdata.get("thumbnail", "")
        emautodel   = wdata.get("autodel", 0) or None

        # embed description  (shown inside the embed card)
        embed_desc = _apply_vars(
            wdata.get("message", "<<user.mention>> Welcome To <<server.name>>"),
            member,
        )

        # plain text content  (shown above the embed, like MIMU)
        raw_text = wdata.get("text", "")
        plain_text = _apply_vars(raw_text, member) if raw_text else ""

        # mention ping overrides plain_text if ping is on and text is empty
        if emping and not plain_text:
            plain_text = member.mention

        # ── build the embed ───────────────────────────────────────
        em = discord.Embed(description=embed_desc, color=0x2f3136)
        em.set_author(
            name=str(member),
            icon_url=member.avatar.url if member.avatar else member.default_avatar.url,
        )
        em.timestamp = discord.utils.utcnow()

        if emimage:
            em.set_image(url=emimage)
        if emthumbnail:
            em.set_thumbnail(url=emthumbnail)
        if member.guild.icon:
            em.set_footer(text=member.guild.name, icon_url=member.guild.icon.url)

        # ── send ──────────────────────────────────────────────────
        for ch_id in channels:
            ch = self.bot.get_channel(int(ch_id))
            if ch is None:
                continue

            if emtog:
                # MIMU-style: plain text + embed in one message
                await ch.send(
                    content=plain_text or None,
                    embed=em,
                    delete_after=emautodel,
                )
            else:
                # Plain text only (embed disabled)
                content = plain_text or embed_desc
                await ch.send(content=content, delete_after=emautodel)
