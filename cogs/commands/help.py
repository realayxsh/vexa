import discord
from discord.ext import commands
from difflib import get_close_matches
from contextlib import suppress
from core import Context
from core.Dilbar import Dilbar
from core.Cog import Cog
from utils.Tools import getConfig
from utils.emojis import e
from itertools import chain
from utils import *
import json
import logging
from utils import help as vhelp
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator

logger = logging.getLogger(__name__)


class HelpCommand(commands.HelpCommand):

    async def on_help_command_error(self, ctx, error):
        original = getattr(error, "original", error)
        logger.error("Help command failed", exc_info=(
            type(original), original, original.__traceback__))
        if isinstance(original, discord.Forbidden):
            # Sending another message to the same channel would fail too.
            return
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f"Please wait {error.retry_after:.1f} seconds before using help again.")
        if isinstance(original, discord.HTTPException):
            return await ctx.send(
                "I couldn't display the help menu. Check my Send Messages, "
                "Embed Links and Use External Emojis permissions. "
                "The error details are in the bot logs.")
        await super().on_help_command_error(ctx, error)

    async def command_not_found(self, string: str) -> str:
        # HelpCommand sends this text itself. Do not fetch unrelated users or
        # rely on a suggestion existing for every misspelled command.
        safe_name = discord.utils.escape_mentions(string)
        matches = get_close_matches(
            string, (str(cmd) for cmd in self.context.bot.walk_commands()))
        message = f"Command `{safe_name}` was not found."
        if matches:
            message += "\nDid you mean: " + ", ".join(f"`{name}`" for name in matches)
        return message

    async def send_bot_help(self, mapping):
        await self.context.typing()
        with open('ignore.json', 'r') as heck:
            randi = json.load(heck)
        with open('blacklist.json', 'r') as f:
            bled = json.load(f)
        if str(self.context.author.id) in bled["ids"]:
            embed = discord.Embed(
                title=f"{e.cross_anim} Blacklisted",
                description=
                "You Are Blacklisted From Using My Commands.\nIf you believe this is a mistake, contact the bot owner.",
                color=0x2f3136)
            return await self.context.reply(embed=embed, mention_author=False)
        elif str(self.context.channel.id) in randi["ids"]:
            return None
        prefix = (getConfig(self.context.guild.id)["prefix"]
                  if self.context.guild else "-")
        filtered = await self.filter_commands(self.context.bot.walk_commands(),
                                              sort=True)
        embed = discord.Embed(
            title="Help Command Overview :",
            description=
            f"{e.dot_white} Prefix for this server is `{prefix}`\n{e.dot_white} Total Commands: {len(set(self.context.bot.walk_commands()))} | Usable by you (here): {len(set(filtered))}\n{e.dot_white} Type `{prefix}help <command | module>` for more info.",
            color=0x2f3136)
        embed.set_thumbnail(url=self.context.bot.user.display_avatar.url)

        embed.set_footer(text="QTs Support",
                         icon_url=self.context.bot.user.display_avatar.url)

        modules = []
        seen_labels = set()
        for cog in mapping:
            help_custom = getattr(cog, "help_custom", None)
            if help_custom is None:
                continue
            _, label, _ = help_custom()
            if label and label not in seen_labels:
                modules.append(f"{e.dot_white} {label}")
                seen_labels.add(label)

        embed.add_field(
            name="__Available Modules__",
            value="\n".join(modules) if modules else "No categorized commands are available.",
            inline=False)
        embed.set_author(name=self.context.author.name,
                         icon_url=self.context.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        view = vhelp.View(mapping=mapping,
                          ctx=self.context,
                          homeembed=embed)
        await self.context.reply(embed=embed, mention_author=False, view=view)

    async def send_command_help(self, command):
        with open('ignore.json', 'r') as heck:
            randi = json.load(heck)
        with open('blacklist.json', 'r') as f:
            data = json.load(f)
        if str(self.context.author.id) in data["ids"]:
            embed = discord.Embed(
                title=f"{e.red_cross} Blacklisted",
                description=
                "You Are Blacklisted From Using My Commands.\nIf you believe this is a mistake, contact the bot owner.",
                color=0x2f3136)
            await self.context.reply(embed=embed, mention_author=False)
        elif str(self.context.channel.id) in randi["ids"]:
            return None
        else:
            hacker = f">>> {command.help}" if command.help else '>>> No Help Provided...'
            embed = discord.Embed(
                description=
                f"""```yaml\n- [] = optional argument\n- <> = required argument\n- Do NOT Type These When Using Commands !```\n{hacker}""",
                color=0x2f3136)
            alias = ' | '.join(command.aliases)

            embed.add_field(
                name="**Aliases**",
                value=f"{alias}" if command.aliases else "No Aliases",
                inline=False)
            embed.add_field(
                name="**Usage**",
                value=f"`{self.context.prefix}{command.signature}`\n")
            embed.set_author(name=f"{command.cog.qualified_name.title()}",
                             icon_url=self.context.bot.user.display_avatar.url)
            await self.context.reply(embed=embed, mention_author=False)

    def get_command_signature(self, command: commands.Command) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = ' | '.join(command.aliases)
            fmt = f'[{command.name} | {aliases}]'
            if parent:
                fmt = f'{parent}'
            alias = f'[{command.name} | {aliases}]'
        else:
            alias = command.name if not parent else f'{parent} {command.name}'
        return f'{alias} {command.signature}'

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f'{command.description}\n\n{command.help}'
        else:
            embed_like.description = command.help or 'No help found...'


    async def send_group_help(self, group):
        with open('blacklist.json', 'r') as f:
            idk = json.load(f)
        with open('ignore.json', 'r') as heck:
            randi = json.load(heck)
        if str(self.context.author.id) in idk["ids"]:
            embed = discord.Embed(
                title=f"{e.red_cross} Blacklisted",
                description=
                "You Are Blacklisted From Using My Commands.\nIf you believe this is a mistake, contact the bot owner.",
                color=0x2f3136)
            await self.context.reply(embed=embed, mention_author=False)
        elif str(self.context.channel.id) in randi["ids"]:
            return None
        else:
            entries = [(
            f"`{self.context.prefix}{cmd.qualified_name}`",
            f"{cmd.short_doc if cmd.short_doc else 'No Description Provided...'}\n\n"
        ) for cmd in group.commands]
        paginator = Paginator(source=FieldPagePaginator(
            entries=entries,
            title=f"{group.qualified_name} Commands",
            description="<...> Duty | [...] Optional\n\n",
            color=0x2f3136,
            per_page=10),
                              ctx=self.context)
        await paginator.paginate()

        
    
    async def send_cog_help(self, cog):
        with open('blacklist.json', 'r') as f:
            data = json.load(f)
        with open('ignore.json', 'r') as heck:
            randi = json.load(heck)
        if str(self.context.author.id) in data["ids"]:
            embed = discord.Embed(
                title=f"{e.red_cross} Blacklisted",
                description=
                "You Are Blacklisted From Using My Commands.\nIf you believe this is a mistake, contact the bot owner.",
                color=0x2f3136)
            return await self.context.reply(embed=embed, mention_author=False)
        elif str(self.context.channel.id) in randi["ids"]:
            return None
        #await self.context.typing()
        entries = [(
            f"`{self.context.prefix}{cmd.qualified_name}`",
            f"{cmd.short_doc if cmd.short_doc else 'No Description Provided...'}\n\n"
        ) for cmd in cog.get_commands()]
        paginator = Paginator(source=FieldPagePaginator(
            entries=entries,
            title=f"{cog.qualified_name.title()} ({len(cog.get_commands())})",
            description="<...> Duty | [...] Optional\n\n",
            color=0x2f3136,
            per_page=10),
                              ctx=self.context)
        await paginator.paginate()


class Help(Cog, name="help"):

    def __init__(self, client: Dilbar):
        self.client = client
        self._original_help_command = client.help_command
        attributes = {
            'name':
            "help",
            'aliases': ['h'],
            'cooldown':
            commands.CooldownMapping.from_cooldown(1, 5,
                                                   commands.BucketType.user),
            'help':
            'Shows help about bot, a command or a category'
        }
        client.help_command = HelpCommand(command_attrs=attributes)
        client.help_command.cog = self

    async def cog_unload(self):
        self.client.help_command = self._original_help_command
