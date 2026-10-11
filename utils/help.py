import discord
from utils.Tools import *
from utils.emojis import e


def component_emoji(value, bot):
  """Omit inaccessible custom emojis rather than sending an invalid component."""
  parsed = discord.PartialEmoji.from_str(str(value))
  if parsed.id is not None and bot.get_emoji(parsed.id) is None:
    return None
  return parsed


class Dropdown(discord.ui.Select):

  def __init__(self, ctx, options):
    super().__init__(placeholder="Please select a page.",
                     min_values=1,
                     max_values=1,
                     options=options)
    self.invoker = ctx.author

  async def callback(self, interaction: discord.Interaction):
    if self.invoker == interaction.user:
      index = self.view.find_index_from_select(self.values[0])
      if not index: index = 0
      await self.view.set_page(index, interaction)
    else:
      await interaction.response.send_message(f"{e.war} Hey its not your session !",
                                              ephemeral=True)


class View(discord.ui.View):

  def __init__(self, mapping: dict, ctx: discord.ext.commands.context.Context,
               homeembed: discord.embeds.Embed):
    super().__init__()
    self.mapping, self.ctx, self.home = mapping, ctx, homeembed
    self.index = 0

    self.options, self.embeds = self.gen_embeds()
    self.add_item(Dropdown(ctx=self.ctx, options=self.options))

  def find_index_from_select(self, value):
    i = 0
    for cog in self.get_cogs():
      if "help_custom" in dir(cog):
        _, label, _ = cog.help_custom()
        if label == value: return i + 1
        i += 1

  def get_cogs(self):
    cogs = []
    for cog in self.mapping.keys():
      cogs.append(cog)
    return cogs

  def gen_embeds(self):
    options, embeds = [], []
    options.append(
      discord.SelectOption(label="Home",
                           emoji=component_emoji(e.dev_anim, self.ctx.bot)))
    embeds.append(self.home)
    for cog in self.get_cogs():
      if "help_custom" in dir(cog):
        emoji, label, description = cog.help_custom()
        options.append(discord.SelectOption(
          label=label, emoji=component_emoji(emoji, self.ctx.bot)))
        embed = discord.Embed(title=f"{emoji} {label} Commands", color=0x2f3136)
        embed.set_footer(
          text="Yawr Support",
          icon_url=
          "https://cdn.discordapp.com/icons/1066734883449340015/18fd7390db5acf2f35635d51617e9e77.png?size=2048"
        )
        for command in cog.get_commands():
          params = ""
          for param in command.clean_params:
            params += f" <{param}>"
          embed.add_field(name=f"{command.name}{params}",
                          value=f"{command.help}\n\u200b",
                          inline=False)
        embeds.append(embed)
    return options, embeds

  async def set_page(self, page: int, interaction: discord.Interaction):
    if 0 <= page < len(self.embeds):
      self.index = page
      await interaction.response.edit_message(
        embed=self.embeds[self.index], view=self)
