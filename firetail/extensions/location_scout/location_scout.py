from discord.ext import commands
from firetail.utils import make_embed

import aiohttp
import json
import operator


class LocationScout:
    """This extension handles price lookups."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='scout', aliases=["recon", "system", "wormhole"])
    async def _scout(self, ctx):
        """Gets you information for systems/wormholes/constellations/regions.
        Use **!scout location** or **!recon location**"""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help scout** for more info.')
        location = ctx.message.content.split(' ', 1)[1]
        data, location_type = await self.get_data(location)
        self.logger.info('Scout - {} requested information for {}'.format(ctx.author, location))
        if data is None:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Could not find a location named {}'.format(location))
        if location_type == 'system':
            await self.format_system(ctx, data)
        elif location_type == 'constellation':
            await self.format_constellation(ctx, data)
        elif location_type == 'region':
            await self.format_region(ctx, data)

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

    async def format_system(self, ctx, data):
        sov_alliance_id = 1
        sov_corp = 'N/A'
        sov_alliance = 'N/A'
        config = self.config
        name = data['name']
        security_status = round(data['security_status'], 1)
        constellation_id = data['constellation_id']
        constellation_data = await self.bot.esi_data.constellation_info(constellation_id)
        constellation_name = constellation_data['name']
        region_id = constellation_data['region_id']
        region_data = await self.bot.esi_data.region_info(region_id)
        region_name = region_data['name']
        planet_count = len(data['planets'])
        if 'stargates' in data:
            stargate_count = len(data['stargates'])
        else:
            stargate_count = 'N/A'
        ship_kills, npc_kills, pod_kills = await self.get_kill_info(data['system_id'])
        sov_battles = await self.get_active_sov_battles()
        active_sov = False
        if security_status < 0.1:
            sov_corp, sov_alliance, sov_alliance_id = await self.get_sov_info(data['system_id'])
            for fights in sov_battles:
                if fights['constellation_id'] == constellation_id:
                    active_sov = True
                    target_system_id = fights['solar_system_id']
                    target_system_info = await self.bot.esi_data.system_info(target_system_id)
                    target_system_name = target_system_info['name']
                    fight_type_raw = fights['event_type']
                    fight_type = fight_type_raw.replace('_', ' ').title()
                    defender_id = fights['defender_id']
                    defender_name = await self.group_name(defender_id)
                    defender_score = fights['defender_score']
                    attacker_score = fights['attackers_score']
                    break
        ship_jumps = await self.get_jump_info(data['system_id'])
        zkill_link = "https://zkillboard.com/system/{}".format(data['system_id'])
        dotlan_link = "http://evemaps.dotlan.net/system/{}".format(name.replace(' ', '_'))
        region_dotlan = "http://evemaps.dotlan.net/map/{}".format(region_name.replace(' ', '_'))
        constellation_dotlan = "http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                            constellation_name.replace(' ', '_'))
        hub_id = [30000142, 30002187, 30002053, 30002659, 30002510]
        report = 'a fairly dead system.'
        if data['system_id'] in hub_id and ship_kills >= 100:
            report = 'a Trade Hub. A high amount of ganking may be occurring at this time.'
        elif data['system_id'] in hub_id:
            report = 'a Trade Hub.'
        elif ship_jumps > 1000 and ship_kills < 25 and npc_kills < 50:
            report = 'a Staging or just had multiple large fleets pass through.'
        elif ship_kills > 150:
            report = 'the sight of a recent large fleet fight.'
        elif ship_kills > 50:
            report = 'the sight of a recent medium fleet fight.'
        elif ship_kills > 25:
            report = 'the sight of a recent small fleet fight.'
        elif npc_kills > 1200 and stargate_count != 'N/A':
            report = 'to have multiple capitals or supercapitals ratting.'
        elif npc_kills > 800 and stargate_count != 'N/A':
            report = 'to have multiple subcap ratting ships or potentially supercarrier ratting.'
        elif npc_kills > 500 and stargate_count != 'N/A':
            report = 'to have multiple subcap ratting ships or potentially carrier ratting.'
        elif npc_kills > 300:
            report = 'to have multiple subcap ratting ships.'
        elif npc_kills > 150:
            report = 'to have a few subcap ratting ships.'
        firetail_intel = '{} is likely {}'.format(name, report)
        embed = make_embed(msg_type='info', title=name,
                           title_url="http://evemaps.dotlan.net/system/{}".format(name.replace(' ', '_')),
                           content='[ZKill]({}) / [Dotlan]({})'.format(zkill_link, dotlan_link))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via firetail Bot")
        embed.set_thumbnail(url='https://imageserver.eveonline.com/Alliance/{}_64.png'.format(sov_alliance_id))
        embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                        inline=False)
        embed.add_field(name="General Info",
                        value='Name:\nRegion:\nConstellation:\nSecurity Status:\nNumber of Planets:'
                              '\nNumber of Gates:')
        embed.add_field(name="-",
                        value='{}\n[{}]({})\n[{}]({})\n{}\n{}\n{}'.format(name, region_name, region_dotlan,
                                                                          constellation_name, constellation_dotlan,
                                                                          security_status, planet_count, stargate_count)
                        , inline=True)
        if sov_alliance != 'N/A' or sov_corp != 'N/A':
            embed.add_field(name="Sov Holders", value='Holding Alliance:\nHolding Corp:')
            embed.add_field(name="-",
                            value='{}\n{}'.format(sov_alliance, sov_corp),
                            inline=True)
        if active_sov is True:
            embed.add_field(name="Active Sov Battle", value='Defender:\nTarget System:\nTarget Structure:'
                                                            '\nDefender Score:\nAttacker Score:')
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}\n{}'.format(defender_name, target_system_name, fight_type,
                                                              defender_score, attacker_score),
                            inline=True)
        embed.add_field(name="Stats For The Last Hour", value='Ship Kills:\nNPC Kills:\nPod Kills:\nShip Jumps:')
        embed.add_field(name="-",
                        value='{}\n{}\n{}\n{}'.format(ship_kills, npc_kills, pod_kills, ship_jumps),
                        inline=True)
        if config.dm_only:
            await ctx.author.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)
        if config.delete_commands:
            await ctx.message.delete()

    async def format_constellation(self, ctx, data):
        config = self.config
        name = data['name']
        region_id = data['region_id']
        region_data = await self.bot.esi_data.region_info(region_id)
        region_name = region_data['name']
        systems = data['systems']
        systems_count = len(data['systems'])
        system_kills = []
        for system in systems:
            ship_kills, npc_kills, pod_kills = await self.get_kill_info(system)
            ship_jumps = await self.get_jump_info(system)
            system_name = await self.bot.esi_data.system_name(system)
            system_kills.append({'system': system_name, "npc_kills": npc_kills, "ship_kills": ship_kills,
                                 "ship_jumps": ship_jumps})
        top_npc_sorted = sorted(system_kills, key=operator.itemgetter("npc_kills"), reverse=True)
        top_ship_sorted = sorted(system_kills, key=operator.itemgetter("ship_kills"), reverse=True)
        sov_battles = await self.get_active_sov_battles()
        active_sov = False
        for fights in sov_battles:
            if fights['constellation_id'] == data['constellation_id']:
                active_sov = True
                target_system_id = fights['solar_system_id']
                target_system_info = await self.bot.esi_data.system_info(target_system_id)
                target_system_name = target_system_info['name']
                fight_type_raw = fights['event_type']
                fight_type = fight_type_raw.replace('_', ' ').title()
                defender_id = fights['defender_id']
                defender_name = await self.group_name(defender_id)
                defender_score = fights['defender_score']
                attacker_score = fights['attackers_score']
                break
        dotlan_link = "http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                   name.replace(' ', '_'))
        region_dotlan = "http://evemaps.dotlan.net/map/{}".format(region_name.replace(' ', '_'))
        embed = make_embed(msg_type='info', title='{} Constellation'.format(name),
                           title_url="http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                                  name.replace(' ', '_')),
                           content='[Dotlan]({})'.format(dotlan_link))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via firetail Bot")
        embed.set_thumbnail(url='https://imageserver.eveonline.com/Alliance/1_64.png')
        embed.add_field(name="General Info",
                        value='Name:\nRegion:\nNumber of Systems:')
        embed.add_field(name="-",
                        value='{}\n[{}]({})\n{}'.format(name, region_name, region_dotlan, systems_count), inline=True)
        if active_sov is True:
            embed.add_field(name="Active Sov Battle", value='Defender:\nTarget System:\nTarget Structure:'
                                                            '\nDefender Score:\nAttacker Score:',
                            inline=False)
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}\n{}'.format(defender_name, target_system_name, fight_type,
                                                              defender_score, attacker_score),
                            inline=True)
        embed.add_field(name="Most NPC's Killed",
                        value='1: {} ({} Killed)\n2: {} ({} Killed)\n3: {} ({} Killed)'.format(
                            top_npc_sorted[0]['system'],
                            top_npc_sorted[0]['npc_kills'],
                            top_npc_sorted[1]['system'],
                            top_npc_sorted[1]['npc_kills'],
                            top_npc_sorted[2]['system'],
                            top_npc_sorted[2]['npc_kills']),
                        inline=False)
        embed.add_field(name="Most Players's Killed",
                        value='1: {} ({} Killed)\n2: {} ({} Killed)\n3: {} ({} Killed)'.format(
                            top_ship_sorted[0]['system'],
                            top_ship_sorted[0]['ship_kills'],
                            top_ship_sorted[1]['system'],
                            top_ship_sorted[1]['ship_kills'],
                            top_ship_sorted[2]['system'],
                            top_ship_sorted[2]['ship_kills']),
                        inline=False)
        if config.dm_only:
            await ctx.author.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)
        if config.delete_commands:
            await ctx.message.delete()

    async def format_region(self, ctx, data):
        config = self.config
        name = data['name']
        constellations = data['constellations']
        constellations_count = len(data['constellations'])
        system_kills = []
        for constellation in constellations:
            constellation_data = await self.bot.esi_data.constellation_info(constellation)
            systems = constellation_data['systems']
            for system in systems:
                ship_kills, npc_kills, pod_kills = await self.get_kill_info(system)
                ship_jumps = await self.get_jump_info(system)
                system_name = await self.bot.esi_data.system_name(system)
                system_kills.append({'system': system_name, "npc_kills": npc_kills, "ship_kills": ship_kills,
                                     "ship_jumps": ship_jumps})
        system_count = len(system_kills)
        top_npc_sorted = sorted(system_kills, key=operator.itemgetter("npc_kills"), reverse=True)
        top_ship_sorted = sorted(system_kills, key=operator.itemgetter("ship_kills"), reverse=True)
        sov_battles = await self.get_active_sov_battles()
        active_sov = False
        for fights in sov_battles:
            if fights['constellation_id'] in data['constellations']:
                active_sov = True
                target_system_id = fights['solar_system_id']
                target_system_info = await self.bot.esi_data.system_info(target_system_id)
                target_system_name = target_system_info['name']
                fight_type_raw = fights['event_type']
                fight_type = fight_type_raw.replace('_', ' ').title()
                defender_id = fights['defender_id']
                defender_name = await self.group_name(defender_id)
                defender_score = fights['defender_score']
                attacker_score = fights['attackers_score']
                break
        dotlan_link = "http://evemaps.dotlan.net/map/{}".format(name.replace(' ', '_'))
        embed = make_embed(msg_type='info', title='{} Region'.format(name),
                           title_url="http://evemaps.dotlan.net/map/{}".format(name.replace(' ', '_')),
                           content='[Dotlan]({})'.format(dotlan_link))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via firetail Bot")
        embed.set_thumbnail(url='https://imageserver.eveonline.com/Alliance/1_64.png')
        embed.add_field(name="General Info",
                        value='Name:\nNumber of Constellations:\nNumber of Systems:')
        embed.add_field(name="-",
                        value='{}\n{}\n{}'.format(name, constellations_count, system_count), inline=True)
        if active_sov is True:
            embed.add_field(name="Active Sov Battle", value='Defender:\nTarget System:\nTarget Structure:'
                                                            '\nDefender Score:\nAttacker Score:')
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}\n{}'.format(defender_name, target_system_name, fight_type,
                                                              defender_score, attacker_score),
                            inline=True)
        embed.add_field(name="Most NPC's Killed",
                        value='1: {} ({} Killed)\n2: {} ({} Killed)\n3: {} ({} Killed)'.format(
                            top_npc_sorted[0]['system'],
                            top_npc_sorted[0]['npc_kills'],
                            top_npc_sorted[1]['system'],
                            top_npc_sorted[1]['npc_kills'],
                            top_npc_sorted[2]['system'],
                            top_npc_sorted[2]['npc_kills']),
                        inline=False)
        embed.add_field(name="Most Players's Killed",
                        value='1: {} ({} Killed)\n2: {} ({} Killed)\n3: {} ({} Killed)'.format(
                            top_ship_sorted[0]['system'],
                            top_ship_sorted[0]['ship_kills'],
                            top_ship_sorted[1]['system'],
                            top_ship_sorted[1]['ship_kills'],
                            top_ship_sorted[2]['system'],
                            top_ship_sorted[2]['ship_kills']),
                        inline=False)
        if config.dm_only:
            await ctx.author.send(embed=embed)
        else:
            await ctx.channel.send(embed=embed)
        if config.delete_commands:
            await ctx.message.delete()

    async def get_kill_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://esi.tech.ccp.is/latest/universe/system_kills/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                ship_kills = 0
                npc_kills = 0
                pod_kills = 0
                for system in data:
                    if system['system_id'] == system_id:
                        ship_kills = system['ship_kills']
                        npc_kills = system['npc_kills']
                        pod_kills = system['pod_kills']
                        break
                return ship_kills, npc_kills, pod_kills

    async def get_jump_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://esi.tech.ccp.is/latest/universe/system_jumps/?datasource=tranquility') as resp:
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

    async def get_active_sov_battles(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://esi.tech.ccp.is/latest/sovereignty/campaigns/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                return data

    async def get_sov_info(self, system_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://esi.tech.ccp.is/latest/sovereignty/map/?datasource=tranquility') as resp:
                data = await resp.text()
                data = json.loads(data)
                sov_alliance_id = 1
                sov_corp = 'N/A'
                sov_alliance = 'N/A'
                for system in data:
                    if system['system_id'] == system_id:
                        if 'corporation_id' in system:
                            sov_corp_id = system['corporation_id']
                            corporation_info = await self.bot.esi_data.corporation_info(sov_corp_id)
                            sov_corp = corporation_info['name']
                        if 'alliance_id' in system:
                            sov_alliance_id = system['alliance_id']
                            alliance_info = await self.bot.esi_data.alliance_info(sov_alliance_id)
                            sov_alliance = alliance_info['name']
                        break
                return sov_corp, sov_alliance, sov_alliance_id

    async def group_name(self, group_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://esi.tech.ccp.is/latest/alliances/{}/?datasource=tranquility'.format(group_id)) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    return data["name"]
                except:
                    return 'Unknown'
