import urllib.request
import json


# Misc

async def esi_search(item, category):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/search/?categories=' + category + '&datasource=tranquility&language=en-us&search=' + item + '&strict=false') as url:
        return json.loads(url.read().decode())


# Character Stuff
async def character_info(characterid):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/characters/' + characterid + '/') as url:
        return json.loads(url.read().decode())


async def character_corp_id(characterid):
    data = await character_info(characterid)
    return data['corporation_id']


async def character_alliance_id(characterid):
    data = await character_info(characterid)
    return data['alliance_id']


async def character_name(characterid):
    data = await character_info(characterid)
    return data['name']


# Item Stuff
async def item_id(itemname):
    with urllib.request.urlopen('https://www.fuzzwork.co.uk/api/typeid.php?typename=' + itemname) as url:
        data = json.loads(url.read().decode())
        return data['typeID']


async def market_data(itemname):
    urlsafe = urllib.parse.quote_plus(itemname)
    itemid = await item_id(urlsafe)
    if itemid == 0:
        return itemid
    else:
        url = 'https://market.fuzzwork.co.uk/aggregates/?station=60003760&types=' + str(itemid)
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
            return data[str(itemid)]
