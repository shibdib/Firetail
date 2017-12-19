from discord.ext import commands
import pytz
from datetime import datetime

from firetail.utils import make_embed


class EveTime:
    """This extension handles the time commands."""

    TIMEZONES = {
        'EVE Time': 'UTC',
        'PST/California': 'America/Los_Angeles',
        'EST/New York': 'America/New_York',
        'CET/Copenhagen': 'Europe/Copenhagen',
        'MSK/Moscow': 'Europe/Moscow',
        'AEST/Sydney': 'Australia/Sydney',
    }

    @commands.command(name='time')
    async def _time(self, ctx):
        """Shows the time in a range of timezones."""
        tz_field = []
        time_field = []
        for display, zone in self.TIMEZONES.items():
            tz_field.append("**{}**".format(display))
            time_field.append(datetime.now(pytz.timezone(zone)).strftime('%H:%M'))

        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.add_field(name="Time Zones", value='\n'.join(tz_field), inline=True)
        embed.add_field(name="Time", value='\n'.join(time_field), inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
