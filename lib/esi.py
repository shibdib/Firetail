import urllib.request
import json


async def character_info(characterid):
    with urllib.request.urlopen('https://esi.tech.ccp.is/latest/characters/' % characterid %'/') as url:
        return json.loads(url.read().decode())


async def character_corp_id(characterid):
    data = character_info(characterid)
    return data['corporation_id']


async def character_alliance_id(characterid):
    data = character_info(characterid)
    return data['alliance_id']


async def character_name(characterid):
    data = character_info(characterid)
    return data['name']

