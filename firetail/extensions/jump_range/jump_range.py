from discord.ext import commands

from firetail.utils import make_embed


class JumpRange:
    """This extension handles the time commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='range')
    async def _range(self, ctx):
        """Provides Jump Range.
        '!range system SHIP' Gives you the JDC/JF 5 range for a ship by default.
        '!range system SHIP 4' This is also possible to declare a JDC besides 5."""
        self.logger.info('JumpRange - {} requested a jump range map.'.format(str(ctx.message.author)))
        try:
            system = ctx.message.content.split(' ')[1].title()
            if '-' in system:
                system = system.upper()
            else:
                system = system.title()
            ship = ctx.message.content.split(' ')[2].title()
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Do !help range for more info')
        try:
            search = 'solar_system'
            system_id = await ctx.bot.esi_data.esi_search(system, search)
            system_id = system_id['solar_system'][0]
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('JumpRange ERROR - {} could not be found'.format(system))
            return await dest.send('**ERROR:** No System Found With The Name {}'.format(system))
        try:
            jdc = ctx.message.content.split(' ')[3]
            if len(jdc) > 1:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                return await dest.send('**ERROR:** Improper JDC skill level'.format(system))
        except:
            jdc = 5
        item_id = await ctx.bot.esi_data.item_id(ship)
        accepted_ship_groups = [898, 659, 485, 547, 902, 30, 1538]
        ship_info = await ctx.bot.esi_data.item_info(item_id)
        ship_group_id = ship_info['group_id']
        if ship_group_id not in accepted_ship_groups:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('JumpRange ERROR - {} is not a Jump Capable Ship'.format(ship))
            return await dest.send('**ERROR:** No Jump Capable Ship Found With The Name {}'.format(ship))
        url = 'http://evemaps.dotlan.net/range/{},{}/{}'.format(ship, jdc, system)
        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot + Dotlan")
        embed.add_field(name="Jump range for a {} from {} with JDC {}".format(ship, system, jdc), value=url)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
