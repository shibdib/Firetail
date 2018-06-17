from discord.ext import commands
import pytz
from datetime import datetime

from firetail.utils import make_embed
from firetail.core import checks


class EveTime:
    """This extension handles the time commands."""

    DEFAULT_TIMEZONES = {
        'Eve Time': 'UTC'
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger


    @commands.command(name='time')
    @checks.spam_check()
    @checks.is_whitelist()
    async def _time(self, ctx):
        """Shows the time in a range of timezones."""
        self.logger.info('EveTime - {} requested time info.'.format(str(ctx.message.author)))
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        try:
            timezones = self.config.timezones
        except AttributeError:
            timezones = DEFAULT_TIMEZONES

        tz_field = []
        time_field = []
        for display, zone in timezones.items():
            tz_field.append("**{}**".format(display))
            time_field.append(datetime.now(pytz.timezone(zone)).strftime('%H:%M'))

        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.add_field(name="Time Zones", value='\n'.join(tz_field), inline=True)
        embed.add_field(name="Time", value='\n'.join(time_field), inline=True)
        await dest.send(embed=embed)
        # Delete the user's command message if configred to
        if self.config.delete_commands:
            await ctx.message.delete()
