import urllib.request
import json


# Misc

async def esi_search(item, category):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/search/?categories=' + str(category) + '&datasource=tranquility&language=en-us&search=' + str(item) + '&strict=false') as url:
        return json.loads(url.read().decode())


async def type_info_search(type_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/universe/types/' + str(type_id) + '/') as url:
        return json.loads(url.read().decode())


async def system_info(system_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/universe/systems/' + str(system_id) + '/') as url:
        return json.loads(url.read().decode())


# Character Stuff
async def character_info(character_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/characters/' + str(character_id) + '/') as url:
        return json.loads(url.read().decode())


async def character_corp_id(character_id):
    data = await character_info(character_id)
    return data['corporation_id']


async def corporation_info(corporation_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/corporations/' + str(corporation_id) + '/') as url:
        return json.loads(url.read().decode())


async def character_alliance_id(character_id):
    data = await character_info(character_id)
    return data['alliance_id']


async def alliance_info(alliance_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/alliances/' + str(alliance_id) + '/') as url:
        return json.loads(url.read().decode())


async def character_name(character_id):
    data = await character_info(character_id)
    return data['name']


# Item Stuff
async def item_id(item_name):
    with urllib.request.urlopen('https://www.fuzzwork.co.uk/api/typeid.php?typename=' + str(item_name)) as url:
        data = json.loads(url.read().decode())
        return data['typeID']


async def market_data(item_name, station):
    urlsafe = urllib.parse.quote_plus(item_name)
    itemid = await item_id(urlsafe)
    if itemid == 0:
        return itemid
    else:
        url = 'https://market.fuzzwork.co.uk/aggregates/?station=' + str(station) + '&types=' + str(itemid)
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
            return data[str(itemid)]
