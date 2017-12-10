from lib import esi


async def run(client, logger, config, message):
    item = message.split()[-1]
    system = message.split()[1]
    data = esi.market_data(item, system)