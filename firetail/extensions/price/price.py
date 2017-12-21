from discord.ext import commands
from firetail.utils import make_embed


class Price:
    """This extension handles price lookups."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    hub_id = {'jita': 60003760,
            'amarr': 60008494,
            'dodixie': 60011866,
            'rens': 60004588,
            'hek': 60005686}

    @commands.command(name='price', aliases=["jita", "amarr", "dodixie", "rens", "hek",])
    async def _price(self, ctx):
        """Gets you price information from the top trade hubs.
        Use **!price item** or **!amarr item** (Works for Jita, Amarr, Dodixie, Rens, Hek)"""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help price** for more info.')
        config = self.config
        item = ctx.message.content.split(' ', 1)[1]
        system = 60003760
        lookup = 'Jita'
        if ctx.message.content.split()[0][len(config.bot_prefix):].lower() != 'price':
            lookup = ctx.message.content.split()[0][len(config.bot_prefix):].lower()
            system = self.hub_id[lookup]
        # handle help request
        if len(ctx.message.content.split()) > 1:
            if ctx.message.content.split(' ', 1)[1].lower() == 'help':
                #  await helptext(client, logger, config, message)
                return
        data = await ctx.bot.esi_data.market_data(item, system)
        self.logger.info('Price - ' + str(ctx.author) + ' requested price information for a ' + str(item))
        if data == 0:
            self.logger.info('Price - ' + str(item) + ' could not be found')
            msg = item + " was not found, are you sure it's an item?"
            if config.dm_only:
                await ctx.author.send(msg)
            else:
                await ctx.channel.send(msg)
            if config.delete_commands:
                await ctx.message.delete()
        else:
            typeid = await ctx.bot.esi_data.item_id(item)
            buymax = '{0:,.2f}'.format(float(data['buy']['max']))
            buymin = '{0:,.2f}'.format(float(data['buy']['min']))
            buyavg = '{0:,.2f}'.format(float(data['buy']['weightedAverage']))
            sellmax = '{0:,.2f}'.format(float(data['sell']['max']))
            sellmin = '{0:,.2f}'.format(float(data['sell']['min']))
            sellavg = '{0:,.2f}'.format(float(data['sell']['weightedAverage']))
            em = make_embed(msg_type='info', title=item.title(),
                            title_url="https://market.fuzzwork.co.uk/type/" + str(typeid) + "/",
                            content="Price information from " + lookup.title())
            em.set_footer(icon_url=ctx.bot.user.avatar_url,
                          text="Provided Via firetail Bot + Fuzzwork Market")
            em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(typeid) + "_64.png")
            em.add_field(name="Buy", value="Low: " + buymin + " \nAvg: " + buyavg + " \nHigh: " + buymax + " \n ",
                         inline=True)
            em.add_field(name="Sell", value="Low: " + sellmin + " \nAvg: " + sellavg + " \nHigh: " + sellmax + " \n ",
                         inline=True)
            if config.dm_only:
                await ctx.author.send(embed=em)
            else:
                await ctx.channel.send(embed=em)
            if config.delete_commands:
                await ctx.message.delete()
