import urllib.request
import json


# Misc

async def esi_search(item, category):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/search/?categories=' + category + '&datasource=tranquility&language=en-us&search=' + item + '&strict=false') as url:
        return json.loads(url.read().decode())


async def type_info_search(type_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/universe/types/' + type_id + '/') as url:
        return json.loads(url.read().decode())


# Character Stuff
async def character_info(character_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/characters/' + character_id + '/') as url:
        return json.loads(url.read().decode())


async def character_corp_id(character_id):
    data = await character_info(character_id)
    return data['corporation_id']


async def corporation_info(corporation_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/corporations/' + corporation_id + '/') as url:
        return json.loads(url.read().decode())


async def character_alliance_id(character_id):
    data = await character_info(character_id)
    return data['alliance_id']


async def alliance_info(alliance_id):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/alliances/' + alliance_id + '/') as url:
        return json.loads(url.read().decode())


async def character_name(character_id):
    data = await character_info(character_id)
    return data['name']


# Item Stuff
async def item_id(item_name):
    with urllib.request.urlopen('https://www.fuzzwork.co.uk/api/typeid.php?typename=' + item_name) as url:
        data = json.loads(url.read().decode())
        return data['typeID']


async def market_data(item_name):
    urlsafe = urllib.parse.quote_plus(item_name)
    itemid = await item_id(urlsafe)
    if itemid == 0:
        return itemid
    else:
        url = 'https://market.fuzzwork.co.uk/aggregates/?station=60003760&types=' + str(itemid)
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
            return data[str(itemid)]
