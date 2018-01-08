import json
import aiohttp

ESI_URL = "https://esi.tech.ccp.is/latest"


class ESI:
    """Data manager for requesting and returning ESI data."""

    def __init__(self, session):
        self.session = session

    async def server_info(self):
        async with aiohttp.ClientSession() as session:
            url = '{}/status/'.format(ESI_URL)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def esi_search(self, item, category):
        async with aiohttp.ClientSession() as session:
            url = ('{}/search/?categories={}&datasource=tranquility'
                   '&language=en-us&search={}&strict=true'
                   '').format(ESI_URL, category, item)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def type_info_search(self, type_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/universe/types/{}/'.format(ESI_URL, type_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def system_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/universe/systems/{}/'.format(ESI_URL, system_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    # Character Stuff

    async def character_info(self, character_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/characters/{}/'.format(ESI_URL, character_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def character_corp_id(self, character_id):
        data = await self.character_info(character_id)
        return data['corporation_id']

    async def corporation_info(self, corporation_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/corporations/{}/'.format(ESI_URL, corporation_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def character_alliance_id(self, character_id):
        data = await self.character_info(character_id)
        return data['alliance_id']

    async def alliance_info(self, alliance_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/alliances/{}/'.format(ESI_URL, alliance_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def character_name(self, character_id):
        data = await self.character_info(character_id)
        return data['name']

    # Item Stuff

    async def item_id(self, item_name):
        async with aiohttp.ClientSession() as session:
            baseurl = 'https://www.fuzzwork.co.uk/api'
            url = '{}/typeid.php?typename={}'.format(baseurl, item_name)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                print(data)
                return data['typeID']

    async def item_info(self, item_id):
        async with aiohttp.ClientSession() as session:
            url = '{}/universe/types/{}/'.format(ESI_URL, item_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def market_data(self, item_name, station):
        itemid = await self.item_id(item_name)
        if itemid == 0:
            return itemid
        else:
            async with aiohttp.ClientSession() as session:
                baseurl = 'https://market.fuzzwork.co.uk/aggregates'
                url = '{}/?station={}&types={}'.format(baseurl, station, itemid)
                async with session.get(url) as resp:
                    data = await resp.text()
                data = json.loads(data)
                return data[str(itemid)]
