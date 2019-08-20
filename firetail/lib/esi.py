import asyncio
import aiohttp

ESI_URL = "https://esi.evetech.net/latest"
FUZZ_URL = "https://www.fuzzwork.co.uk/api"
MARKET_URL = "https://market.fuzzwork.co.uk/aggregates"
OAUTH_URL = "https://login.eveonline.com/oauth/verify"


class ESI:
    """Data manager for requesting and returning ESI data."""

    def __init__(self, session):
        self.session = session
        self._types_cache = {}
        self._celestial_cache = {}
        self._system_cache = {}
        self._constellation_cache = {}
        self._region_cache = {}
        self._planet_cache = {}
        self._station_cache = {}
        self._stargate_cache = {}
        self._star_cache = {}
        self._moon_cache = {}
        self._asteroid_cache = {}

    async def get_data(self, url):
        """Base data retrieval method."""
        async with self.session.get(url) as r:
            try:
                data = await r.json()
            except aiohttp.ContentTypeError:
                await asyncio.sleep(1)
                try:
                    data = await r.json()
                except aiohttp.ContentTypeError:
                    return None
        return data

    async def server_info(self):
        url = '{}/status/'.format(ESI_URL)
        return await self.get_data(url)

    async def esi_search(self, item, category, force_strict=False):
        strict = 'true' if force_strict else 'false'

        url = ('{}/search/?categories={}&datasource=tranquility'
               '&language=en-us&search={}&strict={}')

        data = await self.get_data(url.format(ESI_URL, category, item, strict))

        if category not in data:
            return None

        # if multiple, try stricter search
        if len(data[category]) > 1 and not force_strict:
            strict_data = await self.get_data(url.format(
                ESI_URL, category, item, 'true'))

            # if no strict results, use non-strict results
            if category not in strict_data:
                return data

            data = strict_data

        # TODO: don't return category dict; return result list.
        # example: like `return data[category]`

        return data

    # TODO: `item_info` == `type_info_search`: rename maybe to `type_info`
    async def type_info_search(self, type_id):
        return await self.item_info(type_id)

    # Location Stuff

    # Catch all for unknown ID
    async def celestial_info(self, celestial_id, allow_cache=True):
        if allow_cache:
            if celestial_id in self._celestial_cache:
                return self._celestial_cache[celestial_id]

        location_info = await self.planet_info(celestial_id)
        if 'name' not in location_info.keys():
            location_info = await self.stargate_info(celestial_id)
            if 'name' not in location_info.keys():
                location_info = await self.star_info(celestial_id)
                if 'name' not in location_info.keys():
                    location_info = await self.station_info(celestial_id)
                    if 'name' not in location_info.keys():
                        location_info = await self.moon_info(celestial_id)
                        if 'name' not in location_info.keys():
                            location_info = await self.asteroid_info(celestial_id)
                            if 'name' not in location_info.keys():
                                location_info = {}

        if location_info is not 0:
            self._celestial_cache[celestial_id] = location_info
        return location_info

    async def system_info(self, system_id):
        url = '{}/universe/systems/{}/'.format(ESI_URL, system_id)
        return await self.get_data(url)

    async def system_name(self, system_id):
        url = '{}/universe/systems/{}/'.format(ESI_URL, system_id)
        data = await self.get_data(url)
        if not data:
            return None
        return data.get('name')

    async def constellation_info(self, constellation_id, allow_cache=True):
        if allow_cache:
            if constellation_id in self._constellation_cache:
                return self._constellation_cache[constellation_id]

        url = '{}/universe/constellations/{}/'.format(
            ESI_URL, constellation_id)
        data = await self.get_data(url)
        if data:
            self._constellation_cache[constellation_id] = data
        return data

    async def region_info(self, region_id, allow_cache=True):
        if allow_cache:
            if region_id in self._region_cache:
                return self._region_cache[region_id]

        url = '{}/universe/regions/{}/'.format(ESI_URL, region_id)
        data = await self.get_data(url)
        if data:
            self._region_cache[region_id] = data
        return data

    async def planet_info(self, planet_id, allow_cache=True):
        if allow_cache:
            if planet_id in self._planet_cache:
                return self._planet_cache[planet_id]

        url = '{}/universe/planets/{}/'.format(ESI_URL, planet_id)
        data = await self.get_data(url)
        if data:
            self._planet_cache[planet_id] = data
        return data

    async def moon_info(self, moon_id, allow_cache=True):
        if allow_cache:
            if moon_id in self._moon_cache:
                return self._moon_cache[moon_id]

        url = '{}/universe/moons/{}/'.format(ESI_URL, moon_id)
        data = await self.get_data(url)
        if data:
            self._moon_cache[moon_id] = data
        return data

    async def asteroid_info(self, asteroid_id, allow_cache=True):
        if allow_cache:
            if asteroid_id in self._asteroid_cache:
                return self._asteroid_cache[asteroid_id]

        url = '{}/universe/asteroid_belts/{}/'.format(ESI_URL, asteroid_id)
        data = await self.get_data(url)
        if data:
            self._asteroid_cache[asteroid_id] = data
        return data

    async def stargate_info(self, stargate_id, allow_cache=True):
        if allow_cache:
            if stargate_id in self._stargate_cache:
                return self._stargate_cache[stargate_id]

        url = '{}/universe/stargates/{}/'.format(ESI_URL, stargate_id)
        data = await self.get_data(url)
        if data:
            self._stargate_cache[stargate_id] = data
        return data

    async def star_info(self, star_id, allow_cache=True):
        if allow_cache:
            if star_id in self._star_cache:
                return self._star_cache[star_id]

        url = '{}/universe/stars/{}/'.format(ESI_URL, star_id)
        data = await self.get_data(url)
        if data:
            self._star_cache[star_id] = data
        return data

    async def station_info(self, station_id, allow_cache=True):
        if allow_cache:
            if station_id in self._station_cache:
                return self._station_cache[station_id]

        url = '{}/universe/stations/{}/'.format(ESI_URL, station_id)
        data = await self.get_data(url)
        if data:
            self._station_cache[station_id] = data
        return data

    async def get_jump_info(self, system_id=None):
        url = '{}/universe/system_jumps/'.format(ESI_URL)
        data = await self.get_data(url)
        if not data:
            return None

        if system_id:
            for system in data:
                if system['system_id'] == system_id:
                    return system['ship_jumps']
            return 0
        else:
            return data

    async def get_incursion_info(self):
        url = '{}/incursions/'.format(ESI_URL)
        return await self.get_data(url)

    async def get_active_sov_battles(self):
        url = '{}/sovereignty/campaigns/?datasource=tranquility'
        return await self.get_data(url.format(ESI_URL))

    # Character Stuff

    async def character_info(self, character_id):
        url = '{}/characters/{}/'.format(ESI_URL, character_id)
        return await self.get_data(url)

    async def character_corp_id(self, character_id):
        data = await self.character_info(character_id)
        if not data:
            return None
        return data.get('corporation_id')

    async def corporation_info(self, corporation_id):
        url = '{}/corporations/{}/'.format(ESI_URL, corporation_id)
        return await self.get_data(url)

    async def character_alliance_id(self, character_id):
        data = await self.character_info(character_id)
        if not data:
            return None
        return data.get('alliance_id')

    async def alliance_info(self, alliance_id):
        url = '{}/alliances/{}/'.format(ESI_URL, alliance_id)
        return await self.get_data(url)

    async def character_name(self, character_id):
        data = await self.character_info(character_id)
        if not data:
            return None
        return data.get('name')

    # Item Stuff

    async def item_id(self, item_name):
        url = '{}/typeid.php?typename={}'
        data = await self.get_data(url.format(FUZZ_URL, item_name))
        if not data:
            return None
        return data.get('typeID')

    async def item_info(self, item_id, allow_cache=True):
        if allow_cache:
            if item_id in self._types_cache:
                return self._types_cache[item_id]
        url = '{}/universe/types/{}/'.format(ESI_URL, item_id)
        data = await self.get_data(url)
        if data:
            self._types_cache[item_id] = data
        return data

    async def market_data(self, item_name, station):
        results = await self.esi_search(item_name, 'inventory_type')
        if not results:
            return None

        item_id = results['inventory_type'][0]
        url = '{}/?station={}&types={}'.format(
            MARKET_URL, station, item_id)
        data = await self.get_data(url)
        if not data:
            return None

        return data[str(item_id)]

    # Token Handling

    async def refresh_access_token(self, refresh_token, auth):
        header = {'Authorization': 'Basic {}'.format(auth)}
        params = {'grant_type': 'refresh_token',
                  'refresh_token': refresh_token}

        sess = self.session
        async with sess.get(OAUTH_URL, params=params, headers=header) as r:
            try:
                data = await r.json()
            except aiohttp.ContentTypeError:
                return None
            return data

    async def verify_token(self, access_token):
        header = {'Authorization': 'Bearer {}'.format(access_token)}

        async with self.session.get(OAUTH_URL, headers=header) as r:
            try:
                data = await r.json()
            except aiohttp.ContentTypeError:
                return None
            return data

    # Token Restricted

    async def notifications(self, alliance_id):
        url = '{}/alliances/{}/'.format(ESI_URL, alliance_id)
        return await self.get_data(url)
