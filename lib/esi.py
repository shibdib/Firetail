import aiohttp
import json


# Misc

async def esi_search(item, category):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/search/?categories=' + str(category) + '&datasource=tranquility&language=en-us&search=' + str(item) + '&strict=false'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


async def type_info_search(type_id):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/universe/types/' + str(type_id) + '/'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


async def system_info(system_id):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/universe/systems/' + str(system_id) + '/'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


# Character Stuff
async def character_info(character_id):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/characters/' + str(character_id) + '/'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


async def character_corp_id(character_id):
    data = await character_info(character_id)
    return data['corporation_id']


async def corporation_info(corporation_id):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/corporations/' + str(corporation_id) + '/'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


async def character_alliance_id(character_id):
    data = await character_info(character_id)
    return data['alliance_id']


async def alliance_info(alliance_id):
    async with aiohttp.ClientSession() as session:
        url = 'https://esi.tech.ccp.is/latest/alliances/' + str(alliance_id) + '/'
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data


async def character_name(character_id):
    data = await character_info(character_id)
    return data['name']


# Item Stuff
async def item_id(item_name):
    async with aiohttp.ClientSession() as session:
        url = 'https://www.fuzzwork.co.uk/api/typeid.php?typename=' + str(item_name)
        async with session.get(url) as resp:
            data = await resp.text()
            data = json.loads(data)
            return data['typeID']


async def market_data(item_name, station):
    itemid = await item_id(item_name)
    if itemid == 0:
        return itemid
    else:
        async with aiohttp.ClientSession() as session:
            url = 'https://market.fuzzwork.co.uk/aggregates/?station=' + str(station) + '&types=' + str(itemid)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data[str(itemid)]
