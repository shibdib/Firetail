from lib import esi


async def run(client, logger, config, message):
    item = message.content.split(' ', 1)[1]
    data = await esi.market_data(item)
    if data == 0:
        msg = item + " was not found, are you sure it's an item?".format(message)
        await client.send_message(message.channel, msg)
    else:
        buymax = '{:,}'.format(float(data['buy']['max']))
        buymin = '{:,}'.format(float(data['buy']['min']))
        buyavg = '{:,}'.format(float(data['buy']['weightedAverage']))
        sellmax = '{:,}'.format(float(data['sell']['max']))
        sellmin = '{:,}'.format(float(data['sell']['min']))
        sellavg = '{:,}'.format(float(data['sell']['weightedAverage']))
        raw = """System: **Jita **
Item: **""" + item.capitalize() + """** 

**Buy:** ```Low: """ + buymin + """ 
Avg: """ + buyavg + """ 
High: """ + buymax + """``` 
**Sell:** ```Low: """ + sellmin + """ 
Avg: """ + sellavg + """ 
High: """ + sellmax + """```"""
        msg = raw.format(message)
        await client.send_message(message.channel, msg)


async def helptext(client, logger, config, message):
    msg = "To use this plugin simply do !price itemName. Example **!price rifter**.".format(message)
    await client.send_message(message.channel, msg)