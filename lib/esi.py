import urllib.request
import json


# Misc

async def esi_search(item, category):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/search/?categories=' + category + '&datasource=tranquility&language=en-us&search=' + item + '&strict=false') as url:
        return json.loads(url.read().decode())[0]


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


async def market_data(itemname, systemname):
    itemid = item_id(itemname)
    systemid = esi_search(systemname, 'solarsystem')
    with urllib.request.urlopen('http://api.eve-central.com/api/marketstat?typeid=' + itemid + '&usesystem=' + systemid) as url:
        data = json.loads(url.read().decode())
        return data['typeID']
