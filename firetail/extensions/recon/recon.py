from discord.ext import commands
from firetail.utils import make_embed

import aiohttp
import json

class Recon:
    """This extension handles price lookups."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='recon', aliases=["scout", "system", "wormhole"])
    async def _recon(self, ctx):
        """Gets you information for systems/wormholes/constellations/regions.
        Use **!scout location** or **!recon location**"""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help recon** for more info.')
        location = ctx.message.content.split(' ', 1)[1]
        data, location_type = await self.get_data(location)
        if data is None:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Could not find a location named {}'.format(location))
        if location_type == 'system':
            await self.format_system(ctx, data)
        # elif location_type == 'constellation':
            # self.format_constellation(ctx, data)
        # elif location_type == 'region':
            # self.format_region(ctx, data)

    async def get_data(self, location):
        data = await self.bot.esi_data.esi_search(location, 'solar_system')
        if data is not None and 'solar_system' in data:
            location_type = 'system'
            system_id = data['solar_system'][0]
            system_info = await self.bot.esi_data.system_info(system_id)
            return system_info, location_type
        else:
            data = await self.bot.esi_data.esi_search(location, 'region')
            if data is not None and 'region' in data:
                location_type = 'region'
                region_id = data['region'][0]
                region_info = await self.bot.esi_data.region_info(region_id)
                return region_info, location_type
            else:
                data = await self.bot.esi_data.esi_search(location, 'constellation')
                if data is not None and 'constellation' in data:
                    location_type = 'constellation'
                    constellation_id = data['constellation'][0]
                    constellation_info = await self.bot.esi_data.constellation_info(constellation_id)
                    return constellation_info, location_type
                else:
                    return None, None

    async def get_kill_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://esi.tech.ccp.is/latest/universe/system_kills/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                ship_kills = 0
                npc_kills = 0
                pod_kills = 0
                for system in data:
                    if system['system_id'] == system_id:
                        ship_kills = system['system_id']
                        npc_kills = system['npc_kills']
                        pod_kills = system['pod_kills']
                        break
                return ship_kills, npc_kills, pod_kills

    async def get_jump_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://esi.tech.ccp.is/latest/universe/system_jumps/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                ship_jumps = 0
                for system in data:
                    if system['system_id'] == system_id:
                        ship_jumps = system['ship_jumps']
                return ship_jumps

    async def get_incursion_info(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://esi.tech.ccp.is/latest/incursions/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def get_sov_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://esi.tech.ccp.is/latest/sovereignty/campaigns/?datasource=tranquility') as resp:
                data = await resp.text()
                sov_battles = json.loads(data)
            async with session.get('https://esi.tech.ccp.is/latest/universe/system_jumps/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                sov_corp = 'N/A'
                sov_alliance = 'N/A'
                sov_faction = 'N/A'
                for system in data:
                    if system['system_id'] == system_id:
                        sov_corp = system['corporation_id']
                        sov_alliance = system['alliance_id']
                        sov_faction = system['faction_id']
                        break
                return sov_corp, sov_alliance, sov_faction, sov_battles

    async def format_system(self, ctx, data):
        config = self.config
        name = data['name']
        security_status = round(data['security_status'], 2)
        constellation_id = data['constellation_id']
        constellation_data = await self.bot.esi_data.constellation_info(constellation_id)
        constellation_name = constellation_data['name']
        region_id = constellation_data['region_id']
        region_data = await self.bot.esi_data.region_info(region_id)
        region_name = region_data['name']
        planet_count = len(data['planets'])
        stargate_count = len(data['50000342'])
        ship_kills, npc_kills, pod_kills = await self.get_kill_info(data['system_id'])
        sov_corp, sov_alliance, sov_faction, sov_battles = await self.get_sov_info(data['system_id'])
        active_sov = False
        for fights in sov_battles:
            if fights['constellation_id'] == constellation_id:
                active_sov = True
                target_system_id = fights['solar_system_id']
                target_system_name = await self.bot.esi_data.system_info(target_system_id)['name']
                fight_type = fights['event_type']
                defender_score = fights['defender_score']
                attacker_score = fights['attackers_score']
                break
        ship_jumps = await self.get_jump_info(data['system_id'])
        zkill_link = "https://zkillboard.com/system/{}".format(data['system_id'])
        dotlan_link = "http://evemaps.dotlan.net/system/{}".format(name)
        firetail_intel = 'Placeholders are super cool.'
        embed = make_embed(msg_type='info', title=name,
                        title_url="http://evemaps.dotlan.net/system/{}".format(name),
                        content='[ZKill]({}) / [Dotlan]({})'.format(zkill_link, dotlan_link))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                      text="Provided Via firetail Bot")
        if sov_alliance != 'N/A':
            embed.set_thumbnail(url='https://imageserver.eveonline.com/Alliance/{}_64.png'.format(sov_alliance))
        embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                        inline=False)
        embed.add_field(name="General Info", value='Name:\nRegion:\nConstellation:\nSecurity Status:\nNumber of Planets:'
                        '\nNumber of Gates:', inline=True)
        embed.add_field(name="-", value='{}\n{}\n{}\n{}\n{}\n{}'.format(name, region_name, constellation_name, security_status,
                                                                        planet_count, stargate_count), inline=True)
        embed.add_field(name="Sov Holders", value='Holding Alliance:\nHolding Corp:\nHolding Faction:',
                        inline=True)
        embed.add_field(name="-",
                        value='{}\n{}\n{}'.format(sov_alliance, sov_corp, sov_faction),
                        inline=True)
        if active_sov is True:
            embed.add_field(name="Active Sov Battle In This Constellation", value='Target System:\nTarget Structure:'
                                                                                       '\nDefender Score:\nAttacker Score:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}'.format(target_system_name, fight_type, defender_score, attacker_score),
                            inline=True)
        embed.add_field(name="Misc Stats", value='Ship Kills/hr:\nNPC Kills/hr:\nPod Kills/hr:\nShip Jumps/hr:',
                        inline=True)
        embed.add_field(name="-",
                        value='{}\n{}\n{}\n{}'.format(ship_kills, npc_kills, pod_kills, ship_jumps),
                        inline=True)
        if config.dm_only:
            await ctx.author.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)
        if config.delete_commands:
            await ctx.message.delete()

    # async def format_constellation(self, ctx, data):

    # async def format_region(self, ctx, data):

