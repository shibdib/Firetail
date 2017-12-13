from lib import esi
import discord


async def run(client, logger, config, message):
    item = message.content.split(' ', 1)[1]
    # handle help request
    if item.lower() == 'help':
        await helptext(client, logger, config, message)
        return
    data = await esi.market_data(item)
    logger.info('Price - ' + str(message.author) + ' requested price information for a ' + str(item))
    if data == 0:
        logger.info('Price - ' + str(item) + ' could not be found')
        msg = item + " was not found, are you sure it's an item?".format(message)
        await client.send_message(message.channel, msg)
    else:
        typeid = await esi.item_id(item)
        buymax = '{:,}'.format(float(data['buy']['max']))
        buymin = '{:,}'.format(float(data['buy']['min']))
        buyavg = '{:,}'.format(float(data['buy']['weightedAverage']))
        sellmax = '{:,}'.format(float(data['sell']['max']))
        sellmin = '{:,}'.format(float(data['sell']['min']))
        sellavg = '{:,}'.format(float(data['sell']['weightedAverage']))
        em = discord.Embed(title=item.title(), description="Price information from Jita 4-4", url="https://market.fuzzwork.co.uk/type/" + str(typeid) + "/", colour=0xDEADBF)
        em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + Fuzzwork Market")
        em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(typeid) + "_64.png")
        em.add_field(name="Buy", value="Low: " + buymin + " \nAvg: " + buyavg + " \nHigh: " + buymax + " \n ", inline=True)
        em.add_field(name="Sell", value="Low: " + sellmin + " \nAvg: " + sellavg + " \nHigh: " + sellmax + " \n ", inline=True)
        await client.send_message(message.channel, embed=em)


async def helptext(client, logger, config, message):
    msg = "To use this plugin simply do !price itemName. Example **!price rifter**.".format(message)
    logger.info('Price - ' + str(message.author) + ' requested help for this plugin')
    await client.send_message(message.channel, msg)
