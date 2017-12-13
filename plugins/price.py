from lib import esi
import discord


async def run(client, logger, config, message):
    item = message.content.split(' ', 1)[1]
    system = 60003760
    lookup = 'Jita'
    hubId = {'jita': 60003760,
            'amarr': 60008494,
            'dodixie': 60011866,
            'rens': 60004588,
            'hek': 60005686}
    if message.content.split()[0][len(config.trigger):].lower() is not 'price':
        lookup = message.content.split()[0][len(config.trigger):].lower()
        system = hubId[lookup]
    # handle help request
    if len(message.content.split()) > 1:
        if message.content.split(' ', 1)[1].lower() == 'help':
            await helptext(client, logger, config, message)
            return
    data = await esi.market_data(item, system)
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
        em = discord.Embed(title=item.title(), description="Price information from " + lookup.title(),
                           url="https://market.fuzzwork.co.uk/type/" + str(typeid) + "/", colour=0xDEADBF)
        em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + Fuzzwork Market")
        em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(typeid) + "_64.png")
        em.add_field(name="Buy", value="Low: " + buymin + " \nAvg: " + buyavg + " \nHigh: " + buymax + " \n ",
                     inline=True)
        em.add_field(name="Sell", value="Low: " + sellmin + " \nAvg: " + sellavg + " \nHigh: " + sellmax + " \n ",
                     inline=True)
        if config.forcePrivateMessage:
            await client.send_message(message.author, embed=em)
        else:
            await client.send_message(message.channel, embed=em)
        if config.deleteRequest:
            await client.delete_message(message)


async def helptext(client, logger, config, message):
    msg = "To use this plugin simply do !price itemName. Example **!price rifter** or use a trade hub such as !jita " \
          "!amarr !dodixie !rens or !hek in place of price.".format(message)
    logger.info('Price - ' + str(message.author) + ' requested help for this plugin')
    await client.send_message(message.channel, msg)
