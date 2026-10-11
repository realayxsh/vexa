import discord, json
from discord.ext import commands
from core import Dilbar, Cog, Context

from utils.emojis import e
from utils.permissions import NotServerOwner, NotCoOwnerOrAbove, NotAdminOrAbove

class Errors(Cog):
  def __init__(self, client: Dilbar):
    self.client = client


  @commands.Cog.listener()
  async def on_command_error(self, ctx: Context, error):
    with open('ignore.json', 'r') as heck:
      randi = json.load(heck) 
    with open('blacklist.json', 'r') as f:
      data = json.load(f)
    if isinstance(error, commands.CommandNotFound):
      return

    # ── Yawr Support custom permission errors ───────────────────────────
    elif isinstance(error, NotServerOwner):
      embed = discord.Embed(
        description=f"{e.red_cross} | **Server Owner Only**\nOnly the server owner can use this command.",
        color=0x50101,
      )
      embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
      return await ctx.reply(embed=embed, mention_author=False, delete_after=8)

    elif isinstance(error, NotCoOwnerOrAbove):
      embed = discord.Embed(
        description=f"{e.red_cross} | **No Permission**\nYou need the **Co Owner** role or higher to use this command.",
        color=0x50101,
      )
      embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
      return await ctx.reply(embed=embed, mention_author=False, delete_after=8)

    elif isinstance(error, NotAdminOrAbove):
      embed = discord.Embed(
        description=f"{e.red_cross} | **No Permission**\nYou need the **Admin** role or higher to use this command.",
        color=0x50101,
      )
      embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
      return await ctx.reply(embed=embed, mention_author=False, delete_after=8)

    # ── Standard discord.py errors ───────────────────────────────────────
    elif isinstance(error, commands.MissingRequiredArgument):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
    elif isinstance(error, commands.CheckFailure):
      if str(ctx.author.id) in data["ids"]:
        embed = discord.Embed(title=f"{e.red_cross} Blacklisted", description="You Are Blacklisted From Using My Commands.\nIf you believe this is a mistake, contact the bot owner.", color=0x50101)
        await ctx.reply(embed=embed, mention_author=False)
      if str(ctx.channel.id) in randi["ids"]:
        await ctx.reply(f"My all commands are disabled for {ctx.channel.mention}",mention_author=True, delete_after=6)
    elif isinstance(error, commands.NoPrivateMessage):
      hacker = discord.Embed(color=0x50101,description=f"You Can\'t Use My Commands In Dm(s)", timestamp=ctx.message.created_at)
      hacker.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar}")
      hacker.set_thumbnail(url =f"{ctx.author.avatar}")
      await ctx.reply(embed=hacker,delete_after=20)
    elif isinstance(error, commands.TooManyArguments):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
        
            
    elif isinstance(error, commands.CommandOnCooldown):
      hacker = discord.Embed(color=0x50101,description=f"{e.war} | {ctx.author.name} is on cooldown retry after {error.retry_after:.2f} second(s)", timestamp=ctx.message.created_at)
      hacker.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
      hacker.set_thumbnail(url =f"{ctx.author.avatar}")
      await ctx.reply(embed=hacker,delete_after=10)
    elif isinstance(error, commands.MaxConcurrencyReached):
      hacker = discord.Embed(color=0x50101,description=f"{e.war} | This Command is already going on, let it finish and retry after", timestamp=ctx.message.created_at)
      hacker.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar}")
      hacker.set_thumbnail(url =f"{ctx.author.avatar}")
      await ctx.reply(embed=hacker,delete_after=10)
      ctx.command.reset_cooldown(ctx)
    elif isinstance(error, commands.MissingPermissions):
      missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in error.missing_permissions
            ]
      if len(missing) > 2:
                fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1])
      else:
                fmt = " and ".join(missing)
      hacker = discord.Embed(color=0x50101,description=f"{e.war} | You lack `{fmt}` permission(s) to run `{ctx.command.name}` command!", timestamp=ctx.message.created_at)
      hacker.set_author(name=f"{ctx.author.name}", icon_url=f"{ctx.author.avatar}")
      hacker.set_thumbnail(url =f"{ctx.author.avatar}")
      await ctx.reply(embed=hacker,delete_after=6)
      ctx.command.reset_cooldown(ctx)

    elif isinstance(error, commands.BadArgument):
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)
    elif isinstance(error, commands.BotMissingPermissions):
      missing = ", ".join(error.missing_perms)
      await ctx.send(f'| I need the **{missing}** to run the **{ctx.command.name}** command!', delete_after=10)
      
    elif isinstance(error, discord.HTTPException):
      pass
    elif isinstance(error, commands.CommandInvokeError):
      pass
