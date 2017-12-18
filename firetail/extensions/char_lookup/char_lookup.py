from discord.ext import commands
import pytz
from datetime import datetime

from firetail.utils import make_embed


class CharLookup:
    """This extension handles looking up characters."""

    @commands.command(name='char')
    async def _char(self, ctx):
        """Shows character information. Do '!char name'"""
        character_name = ctx.message.content.split(' ', 1)[1]
        character_id = ctx.bot.esi_data.esi_search(character_name, 'character')
        character_data = ctx.bot.esi_data.character_info(character_id)

        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.add_field(name="Time Zones", value='\n'.join(tz_field), inline=True)
        embed.add_field(name="Time", value='\n'.join(time_field), inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
