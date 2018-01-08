from discord.ext import commands
import pytz
from datetime import datetime

from firetail.utils import make_embed


class JumpPlanner:
    """This extension handles the time commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='jump', alias='route')
    async def _time(self, ctx):
        """Provides a Jump route.
        '!jump system:system' Gives you the JDC 5 Carrier/Super/Fax route by default.
        '!jump system:system SHIP' accepts a different jump capable ship as input
        '!jump system:system SHIP:4' This is also possible to declare a JDC besides 5"""
        self.logger.info('JumpPlanner - {} requested a jump route.'.format(str(ctx.message.author)))
        route = ctx.message.content.split(' ', 1)[1]
        start = route.split(':', 1)[0]
        if '-' in start:
            start = start.upper()
            try:
                search = 'solar_system'
                system_id = await ctx.bot.esi_data.esi_search(start, search)
                system_id = system_id['solar_system'][0]
            except:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} could not be found'.format(start))
                return await dest.send('**ERROR:** No System Found With The Name {}'.format(start))
        end = route.split(':', 1)[1]
        if '-' in end:
            end = end.upper()
            try:
                search = 'solar_system'
                system_id = await ctx.bot.esi_data.esi_search(end, search)
                system_id = system_id['solar_system'][0]
            except:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} could not be found'.format(end))
                return await dest.send('**ERROR:** No System Found With The Name {}'.format(end))
        try:
            variables = ctx.message.content.split(' ', 1)[2]
            ship = variables.split(':', 1)[0]
            item_id = await ctx.bot.esi_data.item_id(ship)
            if item_id == 0:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} could not be found'.format(ship))
                return await dest.send('**ERROR:** No Ship Found With The Name {}'.format(ship))
            jdc = variables.split(':', 1)[1]
            skills = '{}55'.format(jdc)
        except:
            ship = 'Aeon'
            skills = '555'
        url = 'http://evemaps.dotlan.net/jump/{},{}/{}'.format(ship, skills, route)
        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot + Dotlan")
        embed.add_field(name="Jump Route", value=url)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
