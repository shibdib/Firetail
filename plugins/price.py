from lib import esi


async def run(client, logger, config, message):
    item = message.content.split(' ', 1)[1]
    data = await esi.market_data(item)
    buyData = data['buy']
    sellData = data['sell']
    buyMax = '{:,}'.format(float(data['buy']['max']))
    buyMin = '{:,}'.format(float(data['buy']['min']))
    buyAvg = '{:,}'.format(float(data['buy']['weightedAverage']))
    sellMax = '{:,}'.format(float(data['sell']['max']))
    sellMin = '{:,}'.format(float(data['sell']['min']))
    sellAvg = '{:,}'.format(float(data['sell']['weightedAverage']))
    raw = """System: **Jita **
Item: **""" + item.capitalize() + """** 

**Buy:** ```Low: """ + buyMin + """ 
Avg: """ + buyAvg + """ 
High: """ + buyMax + """``` 
**Sell:** ```Low: """ + sellMin + """ 
Avg: """ + sellAvg + """ 
High: """ + sellMax + """```"""
    msg = raw.format(message)
    await client.send_message(message.channel, msg)


async def helpText(client, logger, config, message):
    msg = "To use this plugin simply do !price itemName. Example **!price rifter**.".format(message)
    await client.send_message(message.channel, msg)