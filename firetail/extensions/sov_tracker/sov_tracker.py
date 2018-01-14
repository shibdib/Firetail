from discord.ext import commands
from firetail.lib import db
from firetail.utils import make_embed

import aiohttp
import asyncio
import json
import pytz
from datetime import datetime


class SovTracker:
    """This extension handles price lookups."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                sql = "SELECT * FROM sov_tracker"
                sov_tracking = await db.select(sql)
                sov_battles = await self.get_active_sov_battles()
                for tracked in sov_tracking:
                    active = False
                    for fights in sov_battles:
                        if fights['solar_system_id'] == tracked['system_id'] and fights['event_type'] == tracked['fight_type']:
                            active = True
                            defender_score = fights['defender_score']
                            attacker_score = fights['attackers_score']
                            if defender_score != tracked['defender_score'] or attacker_score != tracked['attacker_score']:
                                system_data = await self.bot.esi_data.system_info(tracked['system_id'])
                                fight_type = fights['fight_type'].replace('_', ' ').title()
                                defender_id = fights['defender_id']
                                defender_name = await self.group_name(defender_id)
                                await self.report_current(system_data, fight_type, defender_name, defender_score,
                                                          attacker_score, None, tracked['channel_id'])
                    if active is False:
                        sql = ''' DELETE FROM sov_tracker WHERE `system_id` = (?) AND `fight_type` = (?) '''
                        values = (tracked['system_id'], tracked['event_type'],)
                        await db.execute_sql(sql, values)
                await asyncio.sleep(120)
            except Exception:
                self.logger.info('ERROR:', exc_info=True)
                await asyncio.sleep(120)

    @commands.command(name='sov', aliases=["wand", "cancer"])
    async def _sov_tracker(self, ctx):
        """Sets the bot to track a sov fight
        `!sov system` to have the bot report every 2 minutes (if it's changed) the latest sov fight scores.
        It will also report upcoming fights."""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help sov** for more info.')
        location = ctx.message.content.split(' ', 1)[1]
        system_data = await self.get_data(location)
        self.logger.info('SovTracker - {} requested information for {}'.format(ctx.author, location))
        if system_data is None:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Could not find a location named {}'.format(location))
        sov_battles = await self.get_active_sov_battles()
        for fights in sov_battles:
            if fights['solar_system_id'] == system_data['system_id']:
                fight_type_raw = fights['event_type']
                fight_type = fight_type_raw.replace('_', ' ').title()
                start_time = datetime.strptime(fights['start_time'], '%Y-%m-%dT%H:%M:%SZ').date()
                current_time = datetime.strptime(str(datetime.now(pytz.timezone('UTC'))), '%Y-%m-%dT%H:%M:%SZ').date()
                defender_id = fights['defender_id']
                defender_name = await self.group_name(defender_id)
                if current_time > start_time:
                    defender_score = fights['defender_score']
                    attacker_score = fights['attackers_score']
                    sql = ''' REPLACE INTO sov_tracker(channel_id,fight_type,system_id,defender_score,attacker_score)
                  VALUES(?,?,?,?,?) '''
                    values = (ctx.channel.id, fight_type_raw, system_data['system_id'], defender_score, attacker_score)
                    await db.execute_sql(sql, values)
                    await self.report_current(system_data, fight_type, defender_name, defender_score,
                                              attacker_score, ctx)
                else:
                    await self.report_upcoming(ctx, system_data, fight_type, defender_name)

    async def get_data(self, location):
        data = await self.bot.esi_data.esi_search(location, 'solar_system')
        if data is not None and 'solar_system' in data:
            system_id = data['solar_system'][0]
            system_info = await self.bot.esi_data.system_info(system_id)
            return system_info
        else:
            return None

    async def report_current(self, system_data, fight_type, defender_name, defender_score, attacker_score, ctx=None,
                             channel_id=None):
            constellation_data = await self.bot.esi_data.constellation_info(system_data['constellation_id'])
            constellation_name = constellation_data['name']
            region_id = constellation_data['region_id']
            region_data = await self.bot.esi_data.region_info(region_id)
            region_name = region_data['name']
            zkill_link = "https://zkillboard.com/system/{}".format(system_data['system_id'])
            dotlan_link = "http://evemaps.dotlan.net/system/{}".format(system_data['name'].replace(' ', '_'))
            constellation_dotlan = "http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                                constellation_name.replace(' ', '_'))
            title = 'Active Sov Battle Reported In: {}'.format(system_data['name'])
            embed = make_embed(msg_type='info', title=title,
                               title_url=dotlan_link,
                               content='[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\nBot will report changes in '
                                       'this battle every 2 minutes.'.
                               format(zkill_link,
                                      system_data['name'],
                                      dotlan_link,
                                      constellation_name,
                                      constellation_dotlan))
            embed.set_footer(icon_url=self.bot.user.avatar_url,
                             text="Provided Via firetail Bot")
            embed.add_field(name="Active Sov Battle", value='Defender:\nFight Type:'
                                                            '\nDefender Score:\nAttacker Score:')
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}'.format(defender_name, fight_type, defender_score, attacker_score),
                            inline=True)
            if ctx is None:
                await ctx.channel.send(embed=embed)
            else:
                channel = self.bot.get_channel(channel_id)
                await channel.send(embed=embed)

    async def report_upcoming(self, ctx, system_data, fight_type, defender_name):
            constellation_data = await self.bot.esi_data.constellation_info(system_data['constellation_id'])
            constellation_name = constellation_data['name']
            region_id = constellation_data['region_id']
            region_data = await self.bot.esi_data.region_info(region_id)
            region_name = region_data['name']
            zkill_link = "https://zkillboard.com/system/{}".format(system_data['system_id'])
            dotlan_link = "http://evemaps.dotlan.net/system/{}".format(system_data['name'].replace(' ', '_'))
            constellation_dotlan = "http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                                constellation_name.replace(' ', '_'))
            title = 'Upcoming Sov Battle In: {}'.format(system_data['name'])
            embed = make_embed(msg_type='info', title=title,
                               title_url=dotlan_link,
                               content='[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\nDo this command again once '
                                       'the battle has begun to receive live updates.'.
                               format(zkill_link,
                                      system_data['name'],
                                      dotlan_link,
                                      constellation_name,
                                      constellation_dotlan))
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via firetail Bot")
            embed.add_field(name="Upcoming Sov Battle", value='Defender:\nFight Type:')
            embed.add_field(name="-",
                            value='{}\n{}'.format(defender_name, fight_type),
                            inline=True)
            await ctx.channel.send(embed=embed)

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
                except Exception:
                    return 'Unknown'
