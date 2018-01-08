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

    @commands.command(name='jump', aliases='route')
    async def _jump(self, ctx):
        """Provides a Jump route.
        '!jump system:system' Gives you the JDC 5 Carrier/Super/Fax route by default.
        '!jump system:system SHIP' accepts a different jump capable ship as input.
        '!jump system:system SHIP:4' This is also possible to declare a JDC besides 5."""
        self.logger.info('JumpPlanner - {} requested a jump route.'.format(str(ctx.message.author)))
        try:
            route = ctx.message.content.split(' ')[1]
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Do !help jump for more info')
        start = route.split(':')[0]
        skills = '555'
        jdc = '5'
        try:
            search = 'solar_system'
            system_id = await ctx.bot.esi_data.esi_search(start, search)
            system_id = system_id['solar_system'][0]
            system_info = await ctx.bot.esi_data.system_info(system_id)
            if system_info['security_status'] >= 0.5:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} is a high sec system'.format(start))
                return await dest.send('**ERROR:** {} is a high sec system.'.format(start))
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('JumpPlanner ERROR - {} could not be found'.format(start))
            return await dest.send('**ERROR:** No System Found With The Name {}'.format(start))
        if '-' in start:
            start = start.upper()
        else:
            start = start.title()
        end = route.split(':')[1]
        end = end.split(' ')[0]
        try:
            search = 'solar_system'
            system_id = await ctx.bot.esi_data.esi_search(end, search)
            system_id = system_id['solar_system'][0]
            system_info = await ctx.bot.esi_data.system_info(system_id)
            if system_info['security_status'] >= 0.5:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} is a high sec system'.format(end))
                return await dest.send('**ERROR:** {} is a high sec system.'.format(end))
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('JumpPlanner ERROR - {} could not be found'.format(end))
            return await dest.send('**ERROR:** No System Found With The Name {}'.format(end))
        if '-' in end:
            end = end.upper()
        else:
            end = end.title()
        if start == end:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('JumpPlanner ERROR - Start and End points were the same'.format(end))
            return await dest.send('**ERROR:** No jumping within the same system'.format(end))
        try:
            variables = ctx.message.content.split(' ')[2]
            if ':' in variables:
                ship = variables.split(':', 1)[0].title()
                jdc = variables.split(':', 1)[1]
                skills = '{}55'.format(jdc)
            else:
                ship = variables.title()
            item_id = await ctx.bot.esi_data.item_id(ship)
            accepted_ship_groups = [898, 659, 485, 547, 902, 30]
            ship_info = await ctx.bot.esi_data.item_info(item_id)
            ship_group_id = ship_info['group_id']
            if ship_group_id not in accepted_ship_groups:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                self.logger.info('JumpPlanner ERROR - {} is not a Jump Capable Ship'.format(ship))
                return await dest.send('**ERROR:** No Jump Capable Ship Found With The Name {}'.format(ship))
        except:
            ship = 'Aeon'
            skills = '555'
        url = 'http://evemaps.dotlan.net/jump/{},{}/{}'.format(ship, skills, route)
        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot + Dotlan")
        embed.add_field(name="Jump route for an {} from {} to {} with JDC {}".format(ship, start, end, jdc), value=url)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
