from __future__ import annotations
from discord.ext import commands
import discord
import aiohttp
import json
import time
import asyncio
import os
import typing
from utils.config import OWNER_IDS, EXTENSIONS, No_Prefix
from utils import getConfig, updateConfig, DotEnv
from utils.permissions import global_permission_check
from .Context import Context
from discord.ext import commands, tasks


class Dilbar(commands.AutoShardedBot):

    def __init__(self, *arg, **kwargs):
        intents = discord.Intents.all()
        super().__init__(command_prefix=self.get_prefix,
                         case_insensitive=True,
                         intents=intents,
                         status=discord.Status.dnd,
                         strip_after_prefix=True,
                         owner_ids=set(OWNER_IDS),
                         allowed_mentions=discord.AllowedMentions(
                             everyone=False, replied_user=False, roles=False),
                         shard_count=1)

    async def setup_hook(self):
        self.add_check(global_permission_check)

    async def on_ready(self):
        print("Connected as {}".format(self.user))

    async def on_connect(self):
        await self.change_presence(status=discord.Status.idle,
                                   activity=discord.Activity(
                                       type=discord.ActivityType.listening,
                                       name='-help'))


    async def send_raw(self, channel_id: int, content: str,
                       **kwargs) -> typing.Optional[discord.Message]:
        await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        """Invoke the help command or default help command if help extensions is not loaded."""
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(
            self, channel: discord.TextChannel,
            messageID: int) -> typing.Optional[discord.Message]:
        async for msg in channel.history(
                limit=1,
                before=discord.Object(messageID + 1),
                after=discord.Object(messageID - 1),
        ):
            return msg

    async def get_prefix(self, message: discord.Message):
        with open('info.json', 'r') as f:
            p = json.load(f)
        if message.author.id in p["np"]:
            return commands.when_mentioned_or('-', '')(self, message)
        else:
            if message.guild:
                data = getConfig(message.guild.id)
                prefix = data["prefix"]
                return commands.when_mentioned_or(prefix)(self, message)
            else:
                return commands.when_mentioned_or('-')(self, message)

    async def on_message_edit(self, before, after):
        ctx: Context = await self.get_context(after, cls=Context)
        if before.content != after.content:
            if after.guild is None or after.author.bot:
                return
            if ctx.command is None:
                return
            await self.invoke(ctx)
        else:
            return
