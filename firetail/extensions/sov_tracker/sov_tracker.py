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
                sov_battles = await self.bot.esi_data.get_active_sov_battles()
                for tracked in sov_tracking:
                    active = False
                    tracked_system_id = tracked[3]
                    tracked_fight_type = tracked[2]
                    system_data = await self.bot.esi_data.system_info(tracked_system_id)
                    for fights in sov_battles:
                        fight_system_id = fights['solar_system_id']
                        fight_fight_type = fights['event_type']
                        if fight_system_id == tracked_system_id and fight_fight_type == tracked_fight_type:
                            active = True
                            defender_score = fights['defender_score']
                            attacker_score = fights['attackers_score']
                            if defender_score != tracked[4] or attacker_score != tracked[5]:
                                fight_type = fights['event_type'].replace('_', ' ').title()
                                defender_id = fights['defender_id']
                                defender_name = await self.group_name(defender_id)
                                if tracked[4] < defender_score:
                                    winning = 1
                                else:
                                    winning = 2
                                await self.report_current(system_data, fight_type, defender_name, defender_score,
                                                          attacker_score, None, tracked[1], winning)
                                sql = ''' UPDATE sov_tracker SET `defender_score` = (?), `attackers_score` = (?) 
                                WHERE `system_id` = (?) AND `fight_type` = (?) '''
                                values = (defender_score, attacker_score, fight_system_id, fight_fight_type,)
                                await db.execute_sql(sql, values)
                    if active is False:
                        sql = ''' DELETE FROM sov_tracker WHERE `system_id` = (?) AND `fight_type` = (?) '''
                        values = (tracked_system_id, tracked_fight_type,)
                        await db.execute_sql(sql, values)
                        if tracked[4] > tracked[5]:
                            winner = 'Defender'
                        else:
                            winner = 'Attacker'
                        await self.report_ended(system_data, tracked_fight_type, winner, tracked[1])
                await asyncio.sleep(60)
            except Exception:
                self.logger.info('ERROR:', exc_info=True)
                await asyncio.sleep(120)

    @commands.command(name='sov', aliases=["wand", "cancer"])
    async def _sov_tracker(self, ctx):
        """Sets the bot to track a sov fight
        `!sov system` to have the bot report every minute (if it's changed) the latest sov fight scores.
        It will also report upcoming fights."""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help sov** for more info.')
        location = ctx.message.content.split(' ')[1]
        if location.lower() == 'remove':
            if len(ctx.message.content.split()) == 2:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                return await dest.send('**ERROR:** To remove a system from tracking do `!sov remove system`')
            location = ctx.message.content.split(' ')[2]
            await self.remove(ctx, location)
        system_data = await self.get_data(location)
        self.logger.info('SovTracker - {} requested information for {}'.format(ctx.author, location))
        if system_data is None:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Could not find a location named {}'.format(location))
        sov_battles = await self.bot.esi_data.get_active_sov_battles()
        for fights in sov_battles:
            if fights['solar_system_id'] == system_data['system_id']:
                fight_type_raw = fights['event_type']
                fight_type = fight_type_raw.replace('_', ' ').title()
                start_time = datetime.strptime(fights['start_time'], '%Y-%m-%dT%H:%M:%SZ')
                time = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ')
                current_time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
                defender_id = fights['defender_id']
                defender_name = await self.group_name(defender_id)
                if current_time > start_time:
                    defender_score = fights['defender_score']
                    attacker_score = fights['attackers_score']
                    sql = ''' REPLACE INTO sov_tracker(channel_id,fight_type,system_id,defender_score,attackers_score)
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
                             channel_id=None, winning=None):
        defender_score = '{}%'.format(defender_score * 100)
        attacker_score = '{}%'.format(attacker_score * 100)
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
        content = '[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\nBot is tracking this battle.'. \
            format(zkill_link,
                   system_data['name'],
                   dotlan_link,
                   constellation_name,
                   constellation_dotlan)
        type = 'info'
        if winning == 1:
            defender_score = '{} :arrow_up:'.format(defender_score)
            attacker_score = '{}'.format(attacker_score)
            title = 'Update For {}'.format(system_data['name'])
            content = '[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\nThe Defender is making progress.'. \
                format(zkill_link,
                       system_data['name'],
                       dotlan_link,
                       constellation_name,
                       constellation_dotlan)
            type = 'success'
        elif winning == 2:
            defender_score = '{}'.format(defender_score)
            attacker_score = '{} :arrow_up:'.format(attacker_score)
            title = 'Update For {}'.format(system_data['name'])
            content = '[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\nThe Attacker is making progress.'. \
                format(zkill_link,
                       system_data['name'],
                       dotlan_link,
                       constellation_name,
                       constellation_dotlan)
            type = 'error'
        embed = make_embed(msg_type=type, title=title,
                           title_url=dotlan_link,
                           content=content)
        embed.set_footer(icon_url=self.bot.user.avatar_url,
                         text="Provided Via firetail Bot")
        embed.add_field(name="Active Sov Battle", value='Defender:\nFight Type:'
                                                        '\nDefender Score:\nAttacker Score:')
        embed.add_field(name="-",
                        value='{}\n{}\n{}\n{}'.format(defender_name, fight_type, defender_score, attacker_score),
                        inline=True)
        try:
            if channel_id is None:
                await ctx.channel.send(embed=embed)
            else:
                channel = self.bot.get_channel(channel_id)
                await channel.send(embed=embed)
        except:
            return None

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

    async def report_ended(self, system_data, tracked_fight_type, winner, channel_id):
        fight_type_raw = tracked_fight_type
        fight_type = fight_type_raw.replace('_', ' ').title()
        constellation_data = await self.bot.esi_data.constellation_info(system_data['constellation_id'])
        constellation_name = constellation_data['name']
        region_id = constellation_data['region_id']
        region_data = await self.bot.esi_data.region_info(region_id)
        region_name = region_data['name']
        zkill_link = "https://zkillboard.com/system/{}".format(system_data['system_id'])
        dotlan_link = "http://evemaps.dotlan.net/system/{}".format(system_data['name'].replace(' ', '_'))
        constellation_dotlan = "http://evemaps.dotlan.net/map/{}/{}".format(region_name.replace(' ', '_'),
                                                                            constellation_name.replace(' ', '_'))
        title = 'Sov Battle In {} has ended.'.format(system_data['name'])
        embed = make_embed(msg_type='info', title=title,
                           title_url=dotlan_link,
                           content='[ZKill]({}) / [{}]({}) / [Constellation: {}]({})\n\nThe {} fight has ended with'
                                   ' the {} claiming victory.'.
                           format(zkill_link,
                                  system_data['name'],
                                  dotlan_link,
                                  constellation_name,
                                  constellation_dotlan,
                                  fight_type,
                                  winner))
        embed.set_footer(icon_url=self.bot.user.avatar_url,
                         text="Provided Via firetail Bot")
        channel = self.bot.get_channel(channel_id)
        try:
            await channel.send(embed=embed)
        except:
            return None

    async def remove(self, ctx, location):
        system_data = await self.get_data(location)
        self.logger.info('SovTracker - {} requested information for {}'.format(ctx.author, location))
        if system_data is None:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Could not find a location named {}'.format(location))
        sql = ''' DELETE FROM sov_tracker WHERE `system_id` = (?) '''
        values = (system_data['system_id'],)
        await db.execute_sql(sql, values)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        return await dest.send('No longer tracking sov battles in {}'.format(system_data['name']))

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
