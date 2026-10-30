from __future__ import annotations
import discord
import asyncio
import os
import logging
from discord.ext import commands
from utils.Tools import *
from utils.emojis import e
from discord.ext.commands import Context
from discord import app_commands
import time
import datetime
import re
from typing import *
from time import strftime
from core import Cog, Dilbar, Context
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format=
    "\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)


class Welcomer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="autorole", invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole.command(name="config")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _ar_config(self, ctx):
        if data := getDB(ctx.guild.id):
            hum = list(data["autorole"]["humans"])
            bo = list(data["autorole"]["bots"])

            fetched_humans: list = []
            fetched_bots: list = []

            #if data["autorole"]["humans"] != []:
            for i in hum:
                role = ctx.guild.get_role(int(i))
                if role is not None:
                    fetched_humans.append(role)

            #if data["autorole"]["bots"] != []:
            for i in bo:
                role = ctx.guild.get_role(int(i))
                if role is not None:
                    fetched_bots.append(role)

            hums = "\n".join(i.mention for i in fetched_humans)
            if not hums:
                hums = " Humans Autorole Not Set."

            bos = "\n".join(i.mention for i in fetched_bots)
            if not bos:
                bos = " Bots Autorole Not Set."

            emb = discord.Embed(
                color=0x2f3136,
                title=f"Autorole of - {ctx.guild.name}").add_field(
                    name="__Humans__", value=hums,
                    inline=False).add_field(name="__Bots__",
                                            value=bos,
                                            inline=False)

            await ctx.send(embed=emb)

    @_autorole.group(name="reset",
                     help="Clear autorole config for the server .")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_reset(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_reset.command(name="humans",
                             help="Clear autorole config for the server .")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_reset(self, ctx):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["humans"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if rl == []:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server don't have any autoroles setupped .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if rl != []:
                    data["autorole"]["humans"] = []
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | Succesfully cleared all human autoroles for {ctx.guild.name} .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole_reset.command(name="bots")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_reset(self, ctx):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["bots"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if rl == []:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server don't have any autoroles setupped .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if rl != []:
                    data["autorole"]["bots"] = []
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | Succesfully cleared all bot autoroles for this server .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole_reset.command(name="all")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_reset_all(self, ctx):
        data = getDB(ctx.guild.id)
        brl = data["autorole"]["bots"]
        hrl = data["autorole"]["humans"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(brl) == 0 and len(hrl) == 0:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server don't have any autoroles setupped .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if hrl != []:
                    data["autorole"]["bots"] = []
                    data["autorole"]["humans"] = []
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | Succesfully cleared all autoroles for this server .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole.group(name="humans", help="Setup autoroles for human users.")
    @blacklist_check()
    @ignore_check()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_humans.command(name="add",
                              help="Add role to list of autorole humans users."
                              )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_add(self, ctx, role: discord.Role):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["humans"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(rl) == 5:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | You have reached maximum channel limit for autorole humans which is five .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if str(role.id) in rl:
                    embed1 = discord.Embed(
                        description=
                        f"{e.red_cross} | {role.mention} is already in human autoroles .",
                        color=0x2f3136)
                    await ctx.send(embed=embed1)
                else:
                    rl.append(str(role.id))
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | {role.mention} has been added to human autoroles .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole_humans.command(
        name="remove", help="Remove a role from autoroles for human users.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_remove(self, ctx, role: discord.Role):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["humans"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(rl) == 0:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server dont have any autrole humans setupped yet .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if str(role.id) not in rl:
                    embed1 = discord.Embed(
                        description="{} is not in human autoroles .".format(
                            role.mention),
                        color=0x2f3136)
                    await ctx.send(embed=embed1)
                else:
                    rl.remove(str(role.id))
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | {role.mention} has been removed from human autoroles .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole.group(name="bots", help="Setup autoroles for bots.")
    @blacklist_check()
    @ignore_check()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_bots.command(name="add",
                            help="Add role to list of autorole bot users.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_add(self, ctx, role: discord.Role):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["bots"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(rl) == 5:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | You have reached maximum role limit for autorole bots which is five.",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if str(role.id) in rl:
                    embed1 = discord.Embed(
                        description=
                        f"{e.red_cross} | {role.mention} is already in bot autoroles.",
                        color=0x2f3136)
                    await ctx.send(embed=embed1)
                else:
                    rl.append(str(role.id))
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | {role.mention} has been added to bot autoroles .",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_autorole_bots.command(name="remove",
                            help="Remove a role from autoroles for bot users.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_remove(self, ctx, role: discord.Role):
        data = getDB(ctx.guild.id)
        rl = data["autorole"]["bots"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(rl) == 0:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server dont have any autrole humans setupped yet .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                if str(role.id) not in rl:
                    embed1 = discord.Embed(
                        description=
                        f"{e.red_cross} | {role.mention} is not in bot autoroles.",
                        color=0x2f3136)
                    await ctx.send(embed=embed1)
                else:
                    rl.remove(str(role.id))
                    updateDB(ctx.guild.id, data)
                    hacker = discord.Embed(
                        description=
                        f"{e.green_tick} | {role.mention} has been removed from bot autoroles.",
                        color=0x2f3136)
                    await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```diff\n - You must have Administrator permission.\n - Your top role should be above my top role. \n```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @commands.hybrid_group(name="greet",
                    aliases=['welcome'],
                    invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_greet.command(name="thumbnail", help="Setups welcome thumbnail .")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_thumbnail(self, ctx, thumbnail_link):
        data = getDB(ctx.guild.id)
        streamables = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if streamables.search(thumbnail_link):
                data["welcome"]["thumbnail"] = thumbnail_link
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Successfully updated the welcome thumbnail url .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            else:
                await ctx.send("Oops, Kindly put a valid link.")
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="image", help="Setups welcome image.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_image(self, ctx, *, image_link):
        data = getDB(ctx.guild.id)
        streamables = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE)

        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if streamables.search(image_link):
                data["welcome"]["image"] = image_link
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Successfully updated the welcome image url .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            else:
                await ctx.send("Oops, Kindly put a valid link.")
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="autodel",
                    help="Automatically delete message after x seconds .")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_autodel(self, ctx, *, autodelete_second):
        data = getDB(ctx.guild.id)
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            data['welcome']['autodel'] = autodelete_second
            updateDB(ctx.guild.id, data)
            hacker = discord.Embed(
                color=0x2f3136,
                description=
                f"{e.green_tick} | Successfully updated the welcome autodelete second to {autodelete_second} .\nFrom now welcome message will be deleted after {autodelete_second} .",
                timestamp=ctx.message.created_at)
            hacker.set_author(name=f"{ctx.author.name}",
                              icon_url=f"{ctx.author.avatar}")
            await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="message", help="Setups welcome message.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_message(self, ctx: commands.Context):
        data = getDB(ctx.guild.id)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            msg = discord.Embed(
                color=0x2f3136,
                description=
                """Here are some keywords, which you can use in your welcome message.\n\nSend your welcome message in this channel now.\n\n\n```xml\n<<server.member_count>> = server member count\n<<server.name>> = server name\n<<user.name>> = username of new member\n<<user.mention>> = mention of the new user\n<<user.created_at>> = creation time of account of user\n<<user.joined_at>> = joining time of the user.\n```"""
            )
            await ctx.send(embed=msg)
            try:
                welcmsg = await self.bot.wait_for('message',
                                                  check=check,
                                                  timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Oops, too late. bye")
                return
            else:
                data["welcome"]["message"] = welcmsg.content
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Successfully updated the welcome message .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="text",
                    help="Set the plain text message sent above the welcome embed (MIMU-style).")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_text(self, ctx: commands.Context):
        data = getDB(ctx.guild.id)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            msg = discord.Embed(
                color=0x2f3136,
                description=(
                    "Send the **plain text** message that appears **above the embed** "
                    "when a member joins.\n\n"
                    "You can use these keywords:\n"
                    "```xml\n"
                    "<<user.mention>>        = mention the new member\n"
                    "<<user.name>>           = username of new member\n"
                    "<<server.name>>         = server name\n"
                    "<<server.member_count>> = total members\n"
                    "```\n"
                    "Send `none` to remove the plain text (embed only)."
                ),
            )
            await ctx.send(embed=msg)
            try:
                reply = await self.bot.wait_for("message", check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Oops, too late. Bye!")
                return
            else:
                new_text = "" if reply.content.lower() == "none" else reply.content
                data["welcome"]["text"] = new_text
                updateDB(ctx.guild.id, data)
                desc = (
                    f"{e.green_tick} | Plain text message removed. Only the embed will be sent."
                    if new_text == ""
                    else f"{e.green_tick} | Plain text message updated successfully."
                )
                hacker = discord.Embed(color=0x2f3136, description=desc,
                                       timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""", color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")
            await ctx.send(embed=hacker5)

    @_greet.command(name="embed", help="Toggle embed for greet message .")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_embed(self, ctx):
        data = getDB(ctx.guild.id)
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if data["welcome"]["embed"] == True:
                data["welcome"]["embed"] = False
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Okay, Now your embed is removed and welcome message will be a plain message .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            elif data["welcome"]["embed"] == False:
                data["welcome"]["embed"] = True
                updateDB(ctx.guild.id, data)
                hacker1 = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Okay, Now your embed is enabled and welcome message will be a embed message.",
                    timestamp=ctx.message.created_at)
                hacker1.set_author(name=f"{ctx.author.name}",
                                   icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker1)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="ping", help="Toggle embed ping for welcomer.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_ping(self, ctx):
        data = getDB(ctx.guild.id)
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if data["welcome"]["ping"] == True:
                data["welcome"]["ping"] = False
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Okay, Now your embed ping is disabled and users won't get pinged upon welcome .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            elif data["welcome"]["ping"] == False:
                data["welcome"]["ping"] = True
                updateDB(ctx.guild.id, data)
                hacker1 = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.green_tick} | Okay, Now your embed ping is enabled and I will ping new users outside the embed .",
                    timestamp=ctx.message.created_at)
                hacker1.set_author(name=f"{ctx.author.name}",
                                   icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker1)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.group(name="channel", help="Setups welcome channel.")
    @blacklist_check()
    @ignore_check()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_channel(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_greet_channel.command(name="add",
                            help="Add a channel to the welcome channels list.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_channel_add(self, ctx, channel: discord.TextChannel):
        data = getDB(ctx.guild.id)
        chh = data["welcome"]["channel"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(chh) == 3:
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.red_cross} | You have reached maximum channel limit for channel which is three .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            else:
                if str(channel.id) in chh:
                    hacker1 = discord.Embed(
                        color=0x2f3136,
                        description=
                        f"{e.red_cross} | This channel is already in the welcome channels list .",
                        timestamp=ctx.message.created_at)
                    hacker1.set_author(name=f"{ctx.author.name}",
                                       icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker1)
                else:
                    chh.append(str(channel.id))
                    updateDB(ctx.guild.id, data)
                    hacker4 = discord.Embed(
                        color=0x2f3136,
                        description=
                        f"{e.green_tick} | Successfully added {channel.mention} to welcome channel list .",
                        timestamp=ctx.message.created_at)
                    hacker4.set_author(name=f"{ctx.author.name}",
                                       icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker4)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet_channel.command(name="remove",
                            help="Remove a chanel from welcome channels list ."
                            )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _greet_channel_remove(self, ctx, channel: discord.TextChannel):
        data = getDB(ctx.guild.id)
        chh = data["welcome"]["channel"]
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if len(chh) == 0:
                hacker = discord.Embed(
                    color=0x2f3136,
                    description=
                    f"{e.red_cross} | This server dont have any welcome channel setupped yet .",
                    timestamp=ctx.message.created_at)
                hacker.set_author(name=f"{ctx.author.name}",
                                  icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker)
            else:
                if str(channel.id) not in chh:
                    hacker1 = discord.Embed(
                        color=0x2f3136,
                        description=
                        f"{e.red_cross} | This channel is not in the welcome channels list .",
                        timestamp=ctx.message.created_at)
                    hacker1.set_author(name=f"{ctx.author.name}",
                                       icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker1)
                else:
                    chh.remove(str(channel.id))
                    updateDB(ctx.guild.id, data)
                    hacker3 = discord.Embed(
                        color=0x2f3136,
                        description=
                        f"{e.green_tick} | Successfully removed {channel.mention} from welcome channel list .",
                        timestamp=ctx.message.created_at)
                    hacker3.set_author(name=f"{ctx.author.name}",
                                       icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker3)
        else:
            hacker5 = discord.Embed(description="""```diff
 - You must have Administrator permission. - Your top role should be above my top role. 
```""",
                                    color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")

            await ctx.send(embed=hacker5)

    @_greet.command(name="test",
                    help="Test the welcome message how it will look like.")
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def welctestt(self, ctx):
        data     = getDB(ctx.guild.id)
        wdata    = data["welcome"]
        chan     = list(wdata.get("channel", []))
        emtog    = wdata.get("embed", False)
        emimage  = wdata.get("image", "")
        emthumb  = wdata.get("thumbnail", "")
        emautodel = wdata.get("autodel", 0) or None
        user     = ctx.author

        if not chan:
            hacker = discord.Embed(
                color=0x2f3136,
                description=f"{e.red_cross} | Oops, Kindly setup your welcome channel first.",
                timestamp=ctx.message.created_at)
            hacker.set_author(name=f"{ctx.author.name}",
                              icon_url=f"{ctx.author.avatar}")
            return await ctx.send(embed=hacker)

        def apply_vars(text):
            replacements = {
                "<<server.name>>":         user.guild.name,
                "<<server.member_count>>": str(user.guild.member_count),
                "<<user.name>>":           str(user),
                "<<user.mention>>":        user.mention,
                "<<user.created_at>>":     f"<t:{int(user.created_at.timestamp())}:F>",
                "<<user.joined_at>>":      f"<t:{int(user.joined_at.timestamp())}:F>",
            }
            for token, value in replacements.items():
                text = text.replace(token, value)
            return text

        embed_desc = apply_vars(
            wdata.get("message", "<<user.mention>> Welcome To <<server.name>>"))
        raw_text   = wdata.get("text", "")
        plain_text = apply_vars(raw_text) if raw_text else ""
        emping     = wdata.get("ping", False)
        if emping and not plain_text:
            plain_text = user.mention

        em = discord.Embed(description=embed_desc, color=0x2f3136)
        em.set_author(name=str(user),
                      icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
        em.timestamp = discord.utils.utcnow()
        if emimage:
            em.set_image(url=emimage)
        if emthumb:
            em.set_thumbnail(url=emthumb)
        if user.guild.icon:
            em.set_footer(text=user.guild.name, icon_url=user.guild.icon.url)

        for ch_id in chan:
            channn = self.bot.get_channel(int(ch_id))
        if channn is None:
            return await ctx.send(f"{e.red_cross} | Could not find the welcome channel.")

        if emtog:
            await channn.send(content=plain_text or None, embed=em, delete_after=emautodel)
        else:
            content = plain_text or embed_desc
            await channn.send(content=content, delete_after=emautodel)

    @_greet.command(name="config", help="Get greet config for the server.")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _config(self, ctx):
        data      = getDB(ctx.guild.id)
        wdata     = data["welcome"]
        msg       = wdata.get("message", "")
        txt       = wdata.get("text", "")
        chan      = list(wdata.get("channel", []))
        emtog     = wdata.get("embed", False)
        emping    = wdata.get("ping", False)
        emimage   = wdata.get("image", "")
        emthumb   = wdata.get("thumbnail", "")
        emautodel = wdata.get("autodel", 0)

        if not chan:
            return await ctx.reply(
                "First setup your greet channel by running `greet channel add #channel`"
            )

        ch_mentions = []
        for chh in chan:
            ch = self.bot.get_channel(int(chh))
            ch_mentions.append(ch.mention if ch else f"`{chh}`")

        embed = discord.Embed(
            color=0x2f3136,
            title=f"Welcome Config — {ctx.guild.name}",
        )
        embed.add_field(name=f"{e.pushpin} Channel(s)",
                        value="\n".join(ch_mentions) or "None", inline=False)
        embed.add_field(name=f"{e.memo} Embed Description (`greet message`)",
                        value=f"```{msg[:200]}```" if msg else "*(default)*", inline=False)
        embed.add_field(name=f"{e.speech_balloon} Plain Text Above Embed (`greet text`)",
                        value=f"```{txt[:200]}```" if txt else "*(not set — mention used if ping is on)*",
                        inline=False)
        embed.add_field(name=f"{e.framed_picture} Embed",
                        value=f"Enabled {e.white_check}" if emtog else f"Disabled {e.cross_mark}", inline=True)
        embed.add_field(name=f"{e.bell} Ping",
                        value=f"Enabled {e.white_check}" if emping else f"Disabled {e.cross_mark}", inline=True)
        embed.add_field(name=f"{e.uptime} Auto Delete",
                        value=f"{emautodel}s" if emautodel else "Off", inline=True)
        if emimage:
            embed.add_field(name=f"{e.framed_picture} Image URL", value=emimage[:80], inline=False)
        if emthumb:
            embed.add_field(name=f"{e.framed_picture} Thumbnail URL", value=emthumb[:80], inline=False)
        if ctx.guild.icon:
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.send(embed=embed)

    @_greet.command(name="reset", help="Clear greet config for the server.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _reset(self, ctx):
        data = getDB(ctx.guild.id)
        if ctx.author == ctx.guild.owner or ctx.author.top_role.position > ctx.guild.me.top_role.position:
            if data["welcome"]["channel"] == []:
                embed = discord.Embed(
                    description=
                    f"{e.red_cross} | This server don't have any greet channel setuped yet .",
                    color=0x2f3136)
                await ctx.send(embed=embed)
            else:
                data["welcome"]["channel"] = []
                data["welcome"]["image"] = ""
                data["welcome"]["message"] = "<<user.mention>> Welcome To <<server.name>>"
                data["welcome"]["text"] = ""
                data["welcome"]["thumbnail"] = ""
                updateDB(ctx.guild.id, data)
                hacker = discord.Embed(
                    description=
                    f"{e.green_tick} | Succesfully cleared all greet config for this server .",
                    color=0x2f3136)
                await ctx.send(embed=hacker)
        else:
            hacker5 = discord.Embed(
                description=
                """```yaml\n - You must have Administrator permission.\n - Your top role should be above my top role.```""",
                color=0x2f3136)
            hacker5.set_author(name=f"{ctx.author.name}",
                               icon_url=f"{ctx.author.avatar}")
            await ctx.send(embed=hacker5)
