from __future__ import annotations
from discord.ext import commands



#____________ Commands ___________

#####################3
from .commands.help import Help
from .commands.general import General
from .commands.moderation import Moderation
from .commands.welcome import Welcomer
from .commands.Afk import afk
from .commands.extra import Utility
from .commands.owner import Owner
from .commands.vcroles import Voice
from .commands.role import Server
from .commands.ignore import Ignore
from .commands.jsk import Jsk
from .commands.setup import Setup
from .commands.stay import Stay
from .commands.embed import EmbedBuilder



#____________ Events _____________
from .events.autoblacklist import AutoBlacklist
from .events.Errors import Errors
from .events.on_guild import Guild
from .events.autorole import Autorole2
from .events.greet2 import greet


##############33cogs#############
from .commands.general1 import devansh102
from .commands.welcome1 import devanshshree3110
from .commands.server import devansh1227
from .commands.mod2 import devansh3110
from .commands.extra1 import devansh2
from .commands.voice import shree00
from .commands.ignore1 import devansh12


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
    await bot.add_cog(General(bot))
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(Welcomer(bot))
    await bot.add_cog(afk(bot))
    await bot.add_cog(Utility(bot))
    voice_cog = Voice(bot)
    await bot.add_cog(voice_cog)
    bot.remove_command("vcrole")
    await bot.add_cog(Owner(bot))
    await bot.add_cog(Server(bot))
    await bot.add_cog(Ignore(bot))
    await bot.add_cog(Jsk(bot))
    await bot.add_cog(Setup(bot))
    await bot.add_cog(Stay(bot))
    await bot.add_cog(EmbedBuilder(bot))

    ####################

    await bot.add_cog(devansh102(bot))
    await bot.add_cog(devanshshree3110(bot))
    await bot.add_cog(devansh1227(bot))
    await bot.add_cog(devansh3110(bot))
    await bot.add_cog(devansh2(bot))
    await bot.add_cog(shree00(bot))
    await bot.add_cog(devansh12(bot))

    ###########################events################

    await bot.add_cog(AutoBlacklist(bot))
    await bot.add_cog(Guild(bot))
    await bot.add_cog(Errors(bot))
    await bot.add_cog(Autorole2(bot))
    await bot.add_cog(greet(bot))
