from __future__ import annotations
from discord.ext import commands
from utils.Tools import *
from utils.emojis import e
from discord import *
from utils.config import OWNER_IDS, No_Prefix
import json, discord
import typing
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator

from typing import Optional


class Owner(commands.Cog):

    def __init__(self, client):
        self.client = client
      
    @commands.command(name="slist")
    @commands.is_owner()
    async def slist(self, ctx):
        devansh37 = ([devansh for devansh in self.client.guilds])
        devansh37 = sorted(devansh37,
                         key=lambda devansh: devansh.member_count,
                         reverse=True)
        entries = [
            f"`[{i}]` | [{g.name}](https://discord.com/channels/{g.id}) - {g.member_count}"
            for i, g in enumerate(devansh37, start=1)
        ]
        paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            description="",
            title=f"Server List of QTs Support - {len(self.client.guilds)}",
            color=0x2f3136,
            per_page=10),
                              ctx=ctx)
        await paginator.paginate()

    



    @commands.command(name="say", help="Make the bot send a message in a channel.", usage="say <#channel> <message>")
    @commands.is_owner()
    async def say(self, ctx, channel: discord.TextChannel, *, message: str):
        try:
            await channel.send(message)
            await ctx.message.add_reaction(e.white_check)
        except discord.Forbidden:
                await ctx.reply(f"{e.cross_mark} I don't have permission to send messages in that channel.")
        except Exception as ex:
                await ctx.reply(f"{e.cross_mark} Error: {ex}")

    @commands.hybrid_command(
        name="setavatar",
        help="Change the bot's profile picture using an uploaded image.",
        usage="setavatar <image attachment>",
    )
    @commands.is_owner()
    async def set_avatar(self, ctx: Context, image: discord.Attachment):
        if image.size > 10 * 1024 * 1024:
            return await ctx.reply(
                f"{e.cross_mark} The image must be 10 MB or smaller.",
                mention_author=False,
            )

        if image.content_type not in {
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
        }:
            return await ctx.reply(
                f"{e.cross_mark} Please attach a PNG, JPEG, GIF, or WebP image.",
                mention_author=False,
            )

        try:
            avatar = await image.read()
            await self.client.user.edit(avatar=avatar)
        except discord.HTTPException as error:
            return await ctx.reply(
                f"{e.cross_mark} Discord couldn't update the bot avatar: `{error}`",
                mention_author=False,
            )

        await ctx.reply(
            f"{e.green_tick} Bot profile picture updated.",
            mention_author=False,
        )

    @commands.hybrid_command(
        name="setbanner",
        help="Change the bot's profile banner using an uploaded image.",
        usage="setbanner <image attachment>",
    )
    @commands.is_owner()
    async def set_banner(self, ctx: Context, image: discord.Attachment):
        if image.size > 10 * 1024 * 1024:
            return await ctx.reply(
                f"{e.cross_mark} The image must be 10 MB or smaller.",
                mention_author=False,
            )

        if image.content_type not in {
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
        }:
            return await ctx.reply(
                f"{e.cross_mark} Please attach a PNG, JPEG, GIF, or WebP image.",
                mention_author=False,
            )

        try:
            banner = await image.read()
            await self.client.user.edit(banner=banner)
        except discord.HTTPException as error:
            return await ctx.reply(
                f"{e.cross_mark} Discord couldn't update the bot banner: `{error}`",
                mention_author=False,
            )

        await ctx.reply(
            f"{e.green_tick} Bot profile banner updated.",
            mention_author=False,
        )

    @commands.command(name="restart", help="Restarts the client.")
    @commands.is_owner()
    async def _restart(self, ctx: Context):
        await ctx.reply("Restarting!")
        restart_program()
      
    @commands.command(name="sync", help="Syncs all database.")
    @commands.is_owner()
    async def _sync(self, ctx):
        await ctx.reply("Syncing...", mention_author=False)
        with open('config.json', 'r') as f:
            data = json.load(f)
        for op in data["guilds"]:
            g = self.client.get_guild(int(op))
            if not g:
                data["guilds"].pop(str(op))
                with open('config.json', 'w') as f:
                    json.dump(data, f, indent=4)

    @commands.group(name="blacklist",
                    help="let's you add someone in blacklist",
                    aliases=["bl"])
    @commands.is_owner()
    async def blacklist(self, ctx):
        if ctx.invoked_subcommand is None:
            with open("blacklist.json") as file:
                blacklist = json.load(file)
                entries = [
                    f"`[{no}]` | <@!{mem}> (ID: {mem})"
                    for no, mem in enumerate(blacklist['ids'], start=1)
                ]
                paginator = Paginator(source=DescriptionEmbedPaginator(
                    entries=entries,
                    title=
                    f"List of Blacklisted users of QTs Support - {len(blacklist['ids'])}",
                    description="",
                    per_page=10,
                    color=0x2f3136),
                                      ctx=ctx)
                await paginator.paginate()

    @blacklist.command(name="add")
    @commands.is_owner()
    async def blacklist_add(self, ctx: Context, member: discord.Member):
        try:
            with open('blacklist.json', 'r') as bl:
                blacklist = json.load(bl)
                if str(member.id) in blacklist["ids"]:
                    embed = discord.Embed(
                        title="Error!",
                        description=f"{member.name} is already blacklisted",
                        color=discord.Colour(0x2f3136))
                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    add_user_to_blacklist(member.id)
                    embed = discord.Embed(
                        title="Blacklisted",
                        description=f"Successfully Blacklisted {member.name}",
                        color=discord.Colour(0x2f3136))
                    with open("blacklist.json") as file:
                        blacklist = json.load(file)
                        embed.set_footer(
                            text=
                            f"There are now {len(blacklist['ids'])} users in the blacklist"
                        )
                        await ctx.reply(embed=embed, mention_author=False)
        except:
            embed = discord.Embed(title="Error!",
                                  description=f"An Error Occurred",
                                  color=discord.Colour(0x2f3136))
            await ctx.reply(embed=embed, mention_author=False)

    @blacklist.command(name="remove")
    @commands.is_owner()
    async def blacklist_remove(self, ctx, member: discord.Member = None):
        try:
            remove_user_from_blacklist(member.id)
            embed = discord.Embed(
                title="User removed from blacklist",
                description=
                f"{e.green_tick} | **{member.name}** has been successfully removed from the blacklist",
                color=0x2f3136)
            with open("blacklist.json") as file:
                blacklist = json.load(file)
                embed.set_footer(
                    text=
                    f"There are now {len(blacklist['ids'])} users in the blacklist"
                )
                await ctx.reply(embed=embed, mention_author=False)
        except:
            embed = discord.Embed(
                title="Error!",
                description=f"**{member.name}** is not in the blacklist.",
                color=0x2f3136)
            embed.set_thumbnail(url=f"{self.client.user.display_avatar.url}")
            await ctx.reply(embed=embed, mention_author=False)

    @commands.group(
        name="np",
        aliases=["noprefix", "no-prefix"],
        help="Allows you to add someone in no prefix list (owner only command)"
    )
    @commands.is_owner()
    async def _np(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @_np.command(name="list", aliases=["all"])
    @commands.is_owner()
    async def np_list(self, ctx):
        with open("info.json") as f:
            np = json.load(f)
            nplist = np["np"]
            npl = ([await self.client.fetch_user(nplu) for nplu in nplist])
            npl = sorted(npl, key=lambda nop: nop.created_at)
            entries = [
                f"`[{no}]` | [{mem}](https://discord.com/users/{mem.id}) (ID: {mem.id})"
                for no, mem in enumerate(npl, start=1)
            ]
            paginator = Paginator(source=DescriptionEmbedPaginator(
                entries=entries,
                title=f"No Prefix of QTs Support - {len(nplist)}",
                description="",
                per_page=10,
                color=0x2f3136),
                                  ctx=ctx)
            await paginator.paginate()

    @_np.command(name="add", help="Add user to no prefix")
    @commands.is_owner()
    async def np_add(self, ctx, user: discord.User):
        with open('info.json', 'r') as idk:
            data = json.load(idk)
        np = data["np"]
        if user.id in np:
            embed = discord.Embed(
                description=
                f"**The User You Provided Already In My No Prefix**",
                color=0x2f3136)
            await ctx.reply(embed=embed)
            return
        else:
            data["np"].append(user.id)
        with open('info.json', 'w') as idk:
            json.dump(data, idk, indent=4)
            embed1 = discord.Embed(
                description=
                f"{e.green_tick} | Added no prefix to {user} for all",
                color=0x2f3136)
          
            await ctx.reply(embed=embed1)

    @_np.command(name="remove", help="Remove user from no prefix")
    @commands.is_owner()
    async def np_remove(self, ctx, user: discord.User):
        with open('info.json', 'r') as idk:
            data = json.load(idk)
        np = data["np"]
        if user.id not in np:
            embed = discord.Embed(
                description="**{} is not in no prefix!**".format(user),
                color=0x2f3136)
            await ctx.reply(embed=embed)
            return
        else:
            data["np"].remove(user.id)
        with open('info.json', 'w') as idk:
            json.dump(data, idk, indent=4)
            embed2 = discord.Embed(
                description=
                f"{e.green_tick} | Removed no prefix from {user} for all",
                color=0x2f3136)

            await ctx.reply(embed=embed2)

    # ── Founder Badge System (slash commands, server-owner only) ─────────

    badge_group = discord.app_commands.Group(
        name="badge",
        description="Manage Founder badges for server members (server owner only)",
        guild_only=True,
    )

    @badge_group.command(name="add", description="Give a member a Founder badge with a server emoji")
    @discord.app_commands.describe(member="The member to give the badge to")
    async def badge_slash_add(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} Only the **server owner** can add badges.", color=0x2f3136),
                ephemeral=True
            )

        guild_emojis = [em for em in interaction.guild.emojis if not em.managed][:25]
        if not guild_emojis:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} This server has no custom emojis to pick from.", color=0x2f3136),
                ephemeral=True
            )

        options = [
            discord.SelectOption(label=em.name, value=str(em.id), emoji=em)
            for em in guild_emojis
        ]

        class EmojiSelectView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.select(placeholder="Pick an emoji for the Founder badge…", options=options)
            async def pick_emoji(self, inner: discord.Interaction, select: discord.ui.Select):
                emoji_id = int(select.values[0])
                emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                badge_str = f"Founder {emoji}"
                existing = getbadges(member.id)
                existing = [b for b in existing if not b.startswith("Founder")]
                existing.append(badge_str)
                makebadges(member.id, existing)
                self.stop()
                await inner.response.edit_message(
                    embed=discord.Embed(
                        description=f"{e.green_tick} | Added **{badge_str}** badge to {member.mention}",
                        color=0x2f3136
                    ),
                    view=None
                )

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Select the emoji for **{member.display_name}**'s Founder badge:",
                color=0x2f3136
            ),
            view=EmojiSelectView(),
            ephemeral=True
        )

    @badge_group.command(name="remove", description="Remove the Founder badge from a member")
    @discord.app_commands.describe(member="The member to remove the badge from")
    async def badge_slash_remove(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} Only the **server owner** can remove badges.", color=0x2f3136),
                ephemeral=True
            )
        existing = getbadges(member.id)
        new_badges = [b for b in existing if not b.startswith("Founder")]
        if len(new_badges) == len(existing):
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} {member.mention} has no Founder badge.", color=0x2f3136),
                ephemeral=True
            )
        makebadges(member.id, new_badges)
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{e.green_tick} | Removed the **Founder** badge from {member.mention}",
                color=0x2f3136
            ),
            ephemeral=True
        )

    @badge_group.command(name="view", description="View the Founder badge of a member")
    @discord.app_commands.describe(member="The member to view the badge of")
    async def badge_slash_view(self, interaction: discord.Interaction, member: discord.Member):
        existing = getbadges(member.id)
        founder = [b for b in existing if b.startswith("Founder")]
        if not founder:
            return await interaction.response.send_message(
            embed=discord.Embed(description=f"{e.cross_mark} {member.mention} has no Founder badge.", color=0x2f3136),
                ephemeral=True
            )
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"**{member.display_name}**'s badge: {founder[0]}",
                color=0x2f3136
            ).set_thumbnail(url=member.display_avatar.url),
            ephemeral=True
        )

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, message: str):
        """ DM the user of your choice """
        try:
            await user.send(message)
            await ctx.send(f"{e.green_tick} | Successfully Sent a DM to **{user}**")
        except discord.Forbidden:
            await ctx.send("This user might be having DMs blocked or it's a bot account...")           



    @commands.group()
    @commands.is_owner()
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))
            
            
    @change.command(name="nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"{e.green_tick} | Successfully changed nickname to **{name}**")
            else:
                await ctx.send(f"{e.green_tick} | Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)



    @commands.command()
    @commands.is_owner()
    async def globalban(self, ctx, *, user: discord.User = None):
        if user is None:
            return await ctx.send(
                "You need to define the user"
            )
        for guild in self.client.guilds:
            for member in guild.members:
                if member == user:
                    await user.ban(reason="lund le lo")
               
        
