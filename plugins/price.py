from lib import esi
import discord


async def run(client, logger, config, message):
    item = message.content.split(' ', 1)[1]
    data = await esi.market_data(item)
    if data == 0:
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
    await client.send_message(message.channel, msg)
