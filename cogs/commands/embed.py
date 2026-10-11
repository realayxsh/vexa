import discord
import asyncio
import re
from discord.ext import commands
from utils.Tools import blacklist_check, ignore_check
from utils.emojis import e
from utils.permissions import server_owner_check, coowner_check
from core import Cog, Dilbar, Context


# ── helpers ──────────────────────────────────────────────────────────────

def _parse_color(value: str) -> int:
    """Turn a hex string like #FF5733 or FF5733 into an int. Returns default on failure."""
    value = value.strip().lstrip("#")
    try:
        return int(value, 16)
    except ValueError:
        return 0x2f3136


URL_RE = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|localhost|\d{1,3}(?:\.\d{1,3}){3})'
    r'(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE
)

def _valid_url(url: str) -> bool:
    return bool(URL_RE.match(url.strip())) if url.strip() else False


# ── Modal: up to 5 fields (Discord limit) ───────────────────────────────

class EmbedModal(discord.ui.Modal, title="Build Your Embed"):
    em_title = discord.ui.TextInput(
        label="Title",
        placeholder="Embed title (leave blank for none)",
        required=False,
        max_length=256,
    )
    em_description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Main body text. Supports Discord markdown.",
        required=False,
        max_length=4000,
    )
    em_color = discord.ui.TextInput(
        label="Color (hex)",
        placeholder="e.g. #FF5733  or  2f3136  (leave blank for default)",
        required=False,
        max_length=10,
    )
    em_footer = discord.ui.TextInput(
        label="Footer text",
        placeholder="Small text at the bottom (optional)",
        required=False,
        max_length=2048,
    )
    em_image = discord.ui.TextInput(
        label="Image URL  (large bottom image, optional)",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=500,
    )

    def __init__(self, target_channel: discord.TextChannel, thumbnail: str = "",
                 author_text: str = "", author_icon: str = "",
                 edit_message: discord.Message = None):
        super().__init__()
        self.target_channel  = target_channel
        self.thumbnail_url   = thumbnail
        self.author_text     = author_text
        self.author_icon_url = author_icon
        self.edit_message    = edit_message   # set when editing an existing embed

    async def on_submit(self, interaction: discord.Interaction):
        color = _parse_color(self.em_color.value) if self.em_color.value.strip() else 0x2f3136

        embed = discord.Embed(
            title=self.em_title.value or None,
            description=self.em_description.value or None,
            color=color,
        )

        if self.author_text:
            icon = self.author_icon_url if _valid_url(self.author_icon_url) else None
            embed.set_author(name=self.author_text, icon_url=icon)

        if self.em_footer.value.strip():
            embed.set_footer(text=self.em_footer.value.strip())

        if _valid_url(self.em_image.value):
            embed.set_image(url=self.em_image.value.strip())

        if _valid_url(self.thumbnail_url):
            embed.set_thumbnail(url=self.thumbnail_url.strip())

        try:
            if self.edit_message:
                await self.edit_message.edit(embed=embed)
                await interaction.response.send_message(
                    f"{e.green_tick} | Embed in {self.edit_message.channel.mention} updated!",
                    ephemeral=True,
                )
            else:
                await self.target_channel.send(embed=embed)
                await interaction.response.send_message(
                    f"{e.green_tick} | Embed sent to {self.target_channel.mention}!",
                    ephemeral=True,
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"{e.red_cross} | I don't have permission to send messages in {self.target_channel.mention}.",
                ephemeral=True,
            )
        except Exception as err:
            await interaction.response.send_message(
                f"{e.red_cross} | Error: `{err}`",
                ephemeral=True,
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            f"{e.red_cross} | Something went wrong: `{error}`", ephemeral=True
        )


class ComponentV2Modal(discord.ui.Modal, title="Build Component V2 Message"):
    em_title = discord.ui.TextInput(
        label="Title",
        placeholder="Message title (optional)",
        required=False,
        max_length=256,
    )
    em_description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="Main message text. Supports Discord markdown.",
        required=False,
        max_length=4000,
    )
    em_color = discord.ui.TextInput(
        label="Accent color (hex)",
        placeholder="e.g. #FF5733 or 2f3136",
        required=False,
        max_length=10,
    )
    em_footer = discord.ui.TextInput(
        label="Footer text",
        placeholder="Optional text at the bottom",
        required=False,
        max_length=2048,
    )
    em_image = discord.ui.TextInput(
        label="Image URL",
        placeholder="https://example.com/image.png (optional)",
        required=False,
        max_length=500,
    )

    def __init__(self, target_channel: discord.TextChannel):
        super().__init__()
        self.target_channel = target_channel

    async def on_submit(self, interaction: discord.Interaction):
        color_text = self.em_color.value.strip().lstrip("#")
        if color_text and not re.fullmatch(r"[0-9a-fA-F]{6}", color_text):
            return await interaction.response.send_message(
                f"{e.red_cross} | Accent color must be a 6-digit hex value, like `#FF5733`.",
                ephemeral=True,
            )
        title = self.em_title.value.strip()
        description = self.em_description.value.strip()
        body = "\n\n".join(
            part for part in (f"## {title}" if title else "", description) if part
        )
        if len(body) > 4000:
            return await interaction.response.send_message(
                f"{e.red_cross} | Title and description together must be at most 4,000 characters.",
                ephemeral=True,
            )

        image_url = self.em_image.value.strip()
        if image_url and not _valid_url(image_url):
            return await interaction.response.send_message(
                f"{e.red_cross} | Please provide a valid image URL.",
                ephemeral=True,
            )

        color = int(color_text, 16) if color_text else 0x2f3136
        container = discord.ui.Container(accent_colour=discord.Colour(color))
        container.add_item(discord.ui.TextDisplay(body or "\u200b"))

        if image_url:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=image_url)
            container.add_item(gallery)

        footer = self.em_footer.value.strip()
        if footer:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"-# {footer}"))

        layout = discord.ui.LayoutView()
        layout.add_item(container)

        try:
            await self.target_channel.send(view=layout)
        except discord.Forbidden:
            return await interaction.response.send_message(
                f"{e.red_cross} | I don't have permission to send messages in {self.target_channel.mention}.",
                ephemeral=True,
            )
        except discord.HTTPException as error:
            return await interaction.response.send_message(
                f"{e.red_cross} | Discord couldn't send the Component V2 message: `{error}`",
                ephemeral=True,
            )

        await interaction.response.send_message(
            f"{e.green_tick} | Component V2 message sent to {self.target_channel.mention}!",
            ephemeral=True,
        )


# ── Button: opens the Modal ──────────────────────────────────────────────

class ComponentV2BuilderView(discord.ui.View):
    def __init__(self, target_channel: discord.TextChannel, invoker: discord.Member):
        super().__init__(timeout=120)
        self.target_channel = target_channel
        self.invoker = invoker

    @discord.ui.button(
        label="Open Component V2 Builder",
        style=discord.ButtonStyle.blurple,
        emoji=e.pencil,
    )
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.invoker.id:
            return await interaction.response.send_message(
                "This builder belongs to someone else.", ephemeral=True
            )
        await interaction.response.send_modal(
            ComponentV2Modal(target_channel=self.target_channel)
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        emoji=e.multiply_sign,
    )
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.invoker.id:
            return await interaction.response.send_message(
                "This builder belongs to someone else.", ephemeral=True
            )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"{e.red_cross} | Component V2 builder cancelled.",
            embed=None,
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class EmbedBuilderView(discord.ui.View):
    def __init__(self, target_channel: discord.TextChannel,
                 thumbnail: str = "", author_text: str = "", author_icon: str = "",
                 invoker: discord.Member = None, edit_message: discord.Message = None):
        super().__init__(timeout=120)
        self.target_channel  = target_channel
        self.thumbnail_url   = thumbnail
        self.author_text     = author_text
        self.author_icon_url = author_icon
        self.invoker         = invoker
        self.edit_message    = edit_message

    @discord.ui.button(label="Open Embed Builder", style=discord.ButtonStyle.blurple,
                emoji=e.pencil)
    async def open_modal(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        if self.invoker and interaction.user.id != self.invoker.id:
            return await interaction.response.send_message(
                "This builder belongs to someone else.", ephemeral=True
            )
        modal = EmbedModal(
            target_channel=self.target_channel,
            thumbnail=self.thumbnail_url,
            author_text=self.author_text,
            author_icon=self.author_icon_url,
            edit_message=self.edit_message,
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji=e.multiply_sign)
    async def cancel(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if self.invoker and interaction.user.id != self.invoker.id:
            return await interaction.response.send_message(
                "This builder belongs to someone else.", ephemeral=True
            )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"{e.red_cross} | Embed builder cancelled.", embed=None, view=self
        )
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


# ── Cog ─────────────────────────────────────────────────────────────────

class EmbedBuilder(Cog):
    """Create and send custom embeds to any channel."""

    def __init__(self, bot: Dilbar):
        self.bot = bot

    # ── main command ────────────────────────────────────────────────────

    @commands.group(
        name="embed",
        aliases=["em"],
        invoke_without_command=True,
        help="Embed builder — create and send rich embeds to any channel.",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def _embed(self, ctx: Context):
        await ctx.send_help(ctx.command)

    # ── embed send ───────────────────────────────────────────────────────

    @_embed.command(
        name="send",
        aliases=["create", "new"],
        help="Build and send an embed to a channel.",
        usage="embed send #channel [--thumbnail <url>] [--author <name>]",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_send(self, ctx: Context, channel: discord.TextChannel,
                         thumbnail: str = "", author: str = ""):
        """
        Opens an interactive embed builder for the specified channel.
        Optional extras:
          thumbnail  — URL of the small top-right image
          author     — Author name shown at the top of the embed
        """
        info_embed = discord.Embed(
            title=f"{e.pencil}  Embed Builder",
            description=(
                f"Click **Open Embed Builder** to fill in your embed details.\n"
                f"The embed will be sent to {channel.mention}.\n\n"
                "**Fields in the modal:**\n"
                "`Title` · `Description` · `Color (hex)` · `Footer` · `Image URL`\n\n"
                "**Extras passed via command:**\n"
                f"Thumbnail: `{thumbnail or 'none'}`\n"
                f"Author: `{author or 'none'}`"
            ),
            color=0x2f3136,
        )
        info_embed.set_footer(text="Expires in 2 minutes")

        view = EmbedBuilderView(
            target_channel=channel,
            thumbnail=thumbnail,
            author_text=author,
            invoker=ctx.author,
        )
        await ctx.reply(embed=info_embed, view=view, mention_author=False)

    @_embed.command(
        name="v2",
        aliases=["components"],
        help="Build and send a Discord Component V2 message to a channel.",
        usage="embed v2 #channel",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_v2(self, ctx: Context, channel: discord.TextChannel):
        info_embed = discord.Embed(
            title=f"{e.pencil} Component V2 Builder",
            description=(
                f"Click **Open Component V2 Builder** to create a message "
                f"for {channel.mention}.\n\n"
                "You can set a title, description, accent color, footer, "
                "and image."
            ),
            color=0x2f3136,
        )
        info_embed.set_footer(text="Expires in 2 minutes")
        await ctx.reply(
            embed=info_embed,
            view=ComponentV2BuilderView(channel, invoker=ctx.author),
            mention_author=False,
        )

    # ── embed edit ───────────────────────────────────────────────────────

    @_embed.command(
        name="edit",
        aliases=["update", "modify"],
        help="Edit an embed that the bot already sent.",
        usage="embed edit <message_id> [#channel]",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_edit(self, ctx: Context, message_id: int,
                         channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        try:
            target_msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | Message `{message_id}` not found in {channel.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )

        if target_msg.author.id != self.bot.user.id:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | I can only edit messages sent by me.",
                    color=0x2f3136,
                ), mention_author=False
            )

        if not target_msg.embeds:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | That message has no embed to edit.",
                    color=0x2f3136,
                ), mention_author=False
            )

        info_embed = discord.Embed(
            title=f"{e.pencil}  Edit Embed",
            description=(
                f"Click **Open Embed Builder** to edit the embed in {channel.mention}.\n"
                f"Message ID: `{message_id}`\n\n"
                "All fields will **replace** the existing embed content."
            ),
            color=0x2f3136,
        )
        info_embed.set_footer(text="Expires in 2 minutes")

        view = EmbedBuilderView(
            target_channel=channel,
            invoker=ctx.author,
            edit_message=target_msg,
        )
        await ctx.reply(embed=info_embed, view=view, mention_author=False)

    # ── embed raw ────────────────────────────────────────────────────────

    @_embed.command(
        name="raw",
        aliases=["quick", "text"],
        help="Send a quick embed with just a title and description (no modal).",
        usage='embed raw #channel <title> | <description>',
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_raw(self, ctx: Context, channel: discord.TextChannel, *, content: str):
        """
        Quickly send an embed using `|` to split title and description.
        Example: -embed raw #general Hello! | This is the description.
        """
        if "|" in content:
            title, _, description = content.partition("|")
            title = title.strip()
            description = description.strip()
        else:
            title = None
            description = content.strip()

        embed = discord.Embed(
            title=title or None,
            description=description or None,
            color=0x2f3136,
        )

        try:
            await channel.send(embed=embed)
            await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.green_tick} | Embed sent to {channel.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )
        except discord.Forbidden:
            await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | I don't have permission to send in {channel.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )

    # ── embed dm ─────────────────────────────────────────────────────────

    @_embed.command(
        name="dm",
        aliases=["direct"],
        help="Send an embed directly to a user's DMs.",
        usage="embed dm @user",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @server_owner_check()
    async def embed_dm(self, ctx: Context, member: discord.Member):
        info_embed = discord.Embed(
            title=f"{e.pencil}  DM Embed Builder",
            description=(
                f"Click **Open Embed Builder** to send an embed to **{member}**'s DMs."
            ),
            color=0x2f3136,
        )
        info_embed.set_footer(text="Expires in 2 minutes")

        # Use their DM channel as the "target" (we'll override send)
        class DmEmbedView(discord.ui.View):
            def __init__(inner_self):
                super().__init__(timeout=120)

            @discord.ui.button(label="Open Embed Builder",
                style=discord.ButtonStyle.blurple, emoji=e.pencil)
            async def open_modal(inner_self, interaction: discord.Interaction,
                                 button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message(
                        "This is not your builder.", ephemeral=True
                    )

                class DmModal(discord.ui.Modal, title="DM Embed"):
                    em_title = discord.ui.TextInput(label="Title", required=False, max_length=256)
                    em_description = discord.ui.TextInput(
                        label="Description", style=discord.TextStyle.long,
                        required=False, max_length=4000,
                    )
                    em_color  = discord.ui.TextInput(label="Color (hex)", required=False, max_length=10)
                    em_footer = discord.ui.TextInput(label="Footer text", required=False, max_length=2048)
                    em_image  = discord.ui.TextInput(label="Image URL", required=False, max_length=500)

                    async def on_submit(s, intr: discord.Interaction):
                        color  = _parse_color(s.em_color.value) if s.em_color.value.strip() else 0x2f3136
                        embed2 = discord.Embed(
                            title=s.em_title.value or None,
                            description=s.em_description.value or None,
                            color=color,
                        )
                        if s.em_footer.value.strip():
                            embed2.set_footer(text=s.em_footer.value.strip())
                        if _valid_url(s.em_image.value):
                            embed2.set_image(url=s.em_image.value.strip())
                        try:
                            await member.send(embed=embed2)
                            await intr.response.send_message(
                                f"{e.green_tick} | Embed sent to **{member}** via DM!", ephemeral=True
                            )
                        except discord.Forbidden:
                            await intr.response.send_message(
                                f"{e.red_cross} | Could not DM **{member}** (DMs may be closed).", ephemeral=True
                            )

                    async def on_error(s, intr, error):
                        await intr.response.send_message(f"Error: {error}", ephemeral=True)

                await interaction.response.send_modal(DmModal())

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji=e.multiply_sign)
            async def cancel(inner_self, interaction: discord.Interaction,
                              button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message(
                        "This is not your builder.", ephemeral=True
                    )
                await interaction.response.edit_message(
                    content=f"{e.red_cross} | Cancelled.", embed=None, view=None
                )
                inner_self.stop()

        await ctx.reply(embed=info_embed, view=DmEmbedView(), mention_author=False)

    # ── embed copy ───────────────────────────────────────────────────────

    @_embed.command(
        name="copy",
        aliases=["clone"],
        help="Copy an existing embed and send it to another channel.",
        usage="embed copy <message_id> <#target_channel> [#source_channel]",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_copy(self, ctx: Context, message_id: int,
                         target: discord.TextChannel,
                         source: discord.TextChannel = None):
        source = source or ctx.channel
        try:
            msg = await source.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | Message `{message_id}` not found in {source.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )

        if not msg.embeds:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | That message has no embed to copy.",
                    color=0x2f3136,
                ), mention_author=False
            )

        try:
            await target.send(embed=msg.embeds[0])
            await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.green_tick} | Embed copied to {target.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )
        except discord.Forbidden:
            await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | No permission to send in {target.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )

    # ── embed delete ─────────────────────────────────────────────────────

    @_embed.command(
        name="delete",
        aliases=["del", "remove"],
        help="Delete a bot message (embed or otherwise) by ID.",
        usage="embed delete <message_id> [#channel]",
    )
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @coowner_check()
    async def embed_delete(self, ctx: Context, message_id: int,
                           channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        try:
            msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | Message `{message_id}` not found in {channel.mention}.",
                    color=0x2f3136,
                ), mention_author=False
            )

        if msg.author.id != self.bot.user.id:
            return await ctx.reply(
                embed=discord.Embed(
                    description=f"{e.red_cross} | I can only delete my own messages.",
                    color=0x2f3136,
                ), mention_author=False
            )

        await msg.delete()
        await ctx.reply(
            embed=discord.Embed(
                description=f"{e.green_tick} | Message `{message_id}` deleted from {channel.mention}.",
                color=0x2f3136,
            ), mention_author=False
        )
