from discord.ext import commands
from firetail.utils import make_embed
from firetail.core import checks


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

    @commands.command(name='price', aliases=["jita", "amarr", "dodixie", "rens", "hek", ])
    @checks.spam_check()
    async def _price(self, ctx):
        """Gets you price information from the top trade hubs.
        Use **!price item** or **!amarr item** (Works for Jita, Amarr, Dodixie, Rens, Hek)"""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help price** for more info.')
        config = self.config
        item = ctx.message.content.split(' ', 1)[1]
        location = 'station=60003760'
        lookup = 'Jita'
        if ctx.message.content.split()[0][len(config.bot_prefix):].lower() != 'price':
            location = None
            lookup = ctx.message.content.split()[0][len(config.bot_prefix):].lower()
            if lookup in self.hub_id:
                location = 'station={}'.format(self.hub_id[lookup])
            else:
                if lookup == 'the':
                    lookup = 'the {}'.format(ctx.message.content.split(' ', 1))
                    item = ctx.message.content.split(' ', 2)[2]
                data = await self.bot.esi_data.esi_search(lookup, 'region')
                if data is not None and data is not False and 'region' in data:
                    location = 'region={}'.format(data['region'][0])
            if location is None:
                msg = "{} was not found, this command only accepts regions and trade hubs".format(lookup)
                if config.dm_only:
                    await ctx.author.send(msg)
                else:
                    await ctx.channel.send(msg)
                if config.delete_commands:
                    await ctx.message.delete()
                return
        data = await ctx.bot.esi_data.market_data(item, location)
        self.logger.info('Price - {} requested price information for a {}'.format(ctx.author, item))
        if data == 0:
            self.logger.info('Price - {} could not be found'.format(item))
            msg = "{} was not found, are you sure it's an item?".format(item)
            if config.dm_only:
                await ctx.author.send(msg)
            else:
                await ctx.channel.send(msg)
            if config.delete_commands:
                await ctx.message.delete()
            return
        else:
            typeid = await ctx.bot.esi_data.item_id(item)
            buymax = '{0:,.2f}'.format(float(data['buy']['max']))
            buymin = '{0:,.2f}'.format(float(data['buy']['min']))
            buyavg = '{0:,.2f}'.format(float(data['buy']['weightedAverage']))
            buy_volume = '{0:,.0f}'.format(float(data['buy']['volume']))
            buy_orders = '{0:,.0f}'.format(float(data['buy']['orderCount']))
            sellmax = '{0:,.2f}'.format(float(data['sell']['max']))
            sellmin = '{0:,.2f}'.format(float(data['sell']['min']))
            sellavg = '{0:,.2f}'.format(float(data['sell']['weightedAverage']))
            sell_volume = '{0:,.0f}'.format(float(data['sell']['volume']))
            sell_orders = '{0:,.0f}'.format(float(data['sell']['orderCount']))
            em = make_embed(msg_type='info', title=item.title(),
                            title_url="https://market.fuzzwork.co.uk/type/{}/".format(typeid),
                            content="Price information from " + lookup.title())
            em.set_footer(icon_url=ctx.bot.user.avatar_url,
                          text="Provided Via firetail Bot + Fuzzwork Market")
            em.set_thumbnail(url="https://image.eveonline.com/Type/{}_64.png".format(typeid))
            em.add_field(name="Buy", value="Low: {}\nAvg: {}\nHigh: {}\nNumber of Orders: {}\nVolume: {}".format(buymin, buyavg, buymax, buy_orders, buy_volume),
                         inline=True)
            em.add_field(name="Sell", value="Low: {}\nAvg: {}\nHigh: {}\nNumber of Orders: {}\nVolume: {}".format(sellmin, sellavg, sellmax, sell_orders, sell_volume),
                         inline=True)
            if config.dm_only:
                await ctx.author.send(embed=em)
            else:
                await ctx.channel.send(embed=em)
            if config.delete_commands:
                await ctx.message.delete()
