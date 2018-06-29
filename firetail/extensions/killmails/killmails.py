from firetail.lib import db
from firetail.utils import make_embed
import asyncio
import json


class Killmails:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.config = bot.config
        self.logger = bot.logger
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                data = await self.request_data()
                if data is not None and 'killID' in data:
                    await self.process_data(data)
                else:
                    await asyncio.sleep(15)
                await asyncio.sleep(1)
            except Exception:
                self.logger.exception('ERROR:')
                await asyncio.sleep(5)

    async def process_data(self, kill_data):
        sent_channels = []
        config = self.config
        km_groups = config.killmail['killmailGroups']
        big_kills = config.killmail['bigKills']
        big_kills_value = config.killmail['bigKillsValue']
        solar_system_id = kill_data['killmail']['solar_system_id']
        self.logger.info(solar_system_id)
        data = await self.bot.esi_data.system_info(solar_system_id)
        constellation_id = data['constellation_id']
        constellation_data = await self.bot.esi_data.constellation_info(constellation_id)
        region_id = constellation_data['region_id']
        #  Foreach thru all provided groups
        for group in km_groups:
            killmail_group_id = int(config.killmail['killmailGroups'][group]['id'])
            channel_id = config.killmail['killmailGroups'][group]['channelId']
            loss = config.killmail['killmailGroups'][group]['lossMails']
            #  Skip npc
            if kill_data['zkb']['npc'] or not kill_data['killmail']['victim']['corporation_id']:
                break
            #  Get all group id's from the mail
            attacker_group_ids = []
            loss_group_ids = []
            if loss:
                loss_group_ids.append(int(kill_data['killmail']['victim']['corporation_id']))
                if 'alliance_id' in kill_data['killmail']['victim']:
                    loss_group_ids.append(int(kill_data['killmail']['victim']['alliance_id']))
            for attacker in kill_data['killmail']['attackers']:
                if 'corporation_id' in attacker:
                    attacker_group_ids.append(int(attacker['corporation_id']))
                if 'alliance_id' in attacker:
                    attacker_group_ids.append(int(attacker['alliance_id']))
            if loss and killmail_group_id in attacker_group_ids and channel_id not in sent_channels:
                sent_channels.append(channel_id)
                await self.process_kill(channel_id, kill_data)
            if killmail_group_id in loss_group_ids and channel_id not in sent_channels:
                sent_channels.append(channel_id)
                await self.process_kill(channel_id, kill_data, False, True)
            for ext in self.bot.extensions:
                if 'add_kills' in ext:
                    sql = "SELECT * FROM add_kills"
                    other_channels = await db.select(sql)
                    for add_kills in other_channels:
                        #  Check if channels are still good and remove if not
                        channel = self.bot.get_channel(int(add_kills[1]))
                        if channel is None:
                            self.logger.exception('Killmail - Bad Channel Attempted removing....')
                            await self.remove_bad_channel(add_kills[1])
                        #  Process added channels and process them if they match
                        if add_kills[3] == region_id and float(kill_data['zkb']['totalValue']) >= \
                                float(add_kills[6]) and add_kills[1] not in sent_channels:
                            sent_channels.append(add_kills[1])
                            await self.process_kill(add_kills[1], kill_data)
                        if add_kills[3] == solar_system_id and float(kill_data['zkb']['totalValue']) >= \
                                float(add_kills[6]) and add_kills[1] not in sent_channels:
                            sent_channels.append(add_kills[1])
                            await self.process_kill(add_kills[1], kill_data)
                        if add_kills[3] in attacker_group_ids and float(kill_data['zkb']['totalValue']) >= \
                                float(add_kills[6]) and add_kills[1] not in sent_channels:
                            sent_channels.append(add_kills[1])
                            await self.process_kill(add_kills[1], kill_data)
                        if add_kills[3] in loss_group_ids and add_kills[5].lower() == 'true' \
                                and float(kill_data['zkb']['totalValue']) >= float(add_kills[6]) \
                                and add_kills[1] not in sent_channels:
                            sent_channels.append(add_kills[1])
                            await self.process_kill(add_kills[1], kill_data, False, True)
                        if add_kills[3] == 9 and float(kill_data['zkb']['totalValue']) >= float(add_kills[6]) \
                                and add_kills[1] not in sent_channels:
                            sent_channels.append(add_kills[1])
                            await self.process_kill(add_kills[1], kill_data, True)
            if kill_data['zkb']['totalValue'] >= big_kills_value and big_kills:
                channel_id = config.killmail['bigKillsChannel']
                await self.process_kill(channel_id, kill_data, True)

    async def process_kill(self, channel_id, kill_data, big=False, loss=False):
        global final_blow_corp_zkill, final_blow_ship_zkill, final_blow_alliance_zkill, final_blow_corp_zkill, final_blow_ship_zkill, final_blow_corp_zkill, final_blow_ship_zkill, final_blow_zkill, final_blow_alliance_zkill, final_blow_corp_zkill, final_blow_ship_zkill, final_blow_zkill, victim_alliance_zkill, victim_zkill, victim_alliance_zkill, victim_zkill
        bot = self.bot
        final_blow_name, final_blow_ship, final_blow_corp, final_blow_alliance = None, None, None, None
        kill_id = kill_data['killID']
        kill_time = kill_data['killmail']['killmail_time'].split('T', 1)[1][:-4]
        value_raw = kill_data['zkb']['totalValue']
        value = '{0:,.2f}'.format(float(value_raw))
        try:
            victim_id = kill_data['killmail']['victim']['character_id']
            victim_name = await self.bot.esi_data.character_name(victim_id)
            victim_zkill = "https://zkillboard.com/character/{}/".format(victim_id)
        except Exception:
            victim_name = None
        ship_lost_id = kill_data['killmail']['victim']['ship_type_id']
        ship_lost_raw = await self.bot.esi_data.type_info_search(ship_lost_id)
        ship_lost = ship_lost_raw['name']
        victim_corp_id = kill_data['killmail']['victim']['corporation_id']
        victim_corp_raw = await self.bot.esi_data.corporation_info(victim_corp_id)
        victim_corp = victim_corp_raw['name']
        victim_corp_zkill = "https://zkillboard.com/corporation/{}/".format(victim_corp_id)
        try:
            victim_alliance_id = kill_data['killmail']['victim']['alliance_id']
            victim_alliance_raw = await self.bot.esi_data.alliance_info(victim_alliance_id)
            victim_alliance = victim_alliance_raw['name']
            victim_alliance_zkill = "https://zkillboard.com/alliance/{}/".format(victim_alliance_id)
        except Exception:
            victim_alliance = None
        attacker_count = 0
        for attacker in kill_data['killmail']['attackers']:
            attacker_count = attacker_count + 1
            if attacker['final_blow']:
                try:
                    final_blow_id = attacker['character_id']
                    final_blow_name = await self.bot.esi_data.character_name(final_blow_id)
                    final_blow_zkill = "https://zkillboard.com/character/{}/".format(final_blow_id)
                except Exception:
                    final_blow_name = None
                try:
                    final_blow_ship_id = attacker['ship_type_id']
                    final_blow_ship_raw = await self.bot.esi_data.type_info_search(final_blow_ship_id)
                    final_blow_ship_zkill = "https://zkillboard.com/ship/{}/".format(final_blow_ship_id)
                    final_blow_ship = final_blow_ship_raw['name']
                except Exception:
                    final_blow_ship = 'UNK'
                    final_blow_ship_zkill = "https://zkillboard.com/ship/1/"
                final_blow_corp_id = attacker['corporation_id']
                final_blow_corp_raw = await self.bot.esi_data.corporation_info(final_blow_corp_id)
                final_blow_corp = final_blow_corp_raw['name']
                final_blow_corp_zkill = "https://zkillboard.com/corporation/{}/".format(final_blow_corp_id)
                try:
                    final_blow_alliance_id = attacker['alliance_id']
                    final_blow_alliance_raw = await self.bot.esi_data.alliance_info(final_blow_alliance_id)
                    final_blow_alliance = final_blow_alliance_raw['name']
                    final_blow_alliance_zkill = "https://zkillboard.com/alliance/{}/".format(final_blow_alliance_id)
                except Exception:
                    final_blow_alliance = None
                break
        solar_system_id = kill_data['killmail']['solar_system_id']
        solar_system_info = await self.bot.esi_data.system_info(solar_system_id)
        solar_system_name = solar_system_info['name']
        location_id = kill_data['zkb']['locationID']
        location_info = await self.bot.esi_data.planet_info(location_id)
        location_name = location_info['name']
        solo = kill_data['zkb']['solo']
        awox = kill_data['zkb']['awox']
        special_info = ''
        if awox:
            special_info = '**~Possible AWOX~**'
        elif solo:
            special_info = '**~Solo kill~**'
        killmail_zkill = "https://zkillboard.com/kill/{}/".format(kill_id)
        if '-' in solar_system_name:
            solar_system_name = solar_system_name.upper()
        title = "{} Destroyed in {}".format(ship_lost, solar_system_name)
        message_type = 'success'
        if big:
            title = "BIG KILL REPORTED: {} Destroyed in {}".format(ship_lost, solar_system_name)
            message_type = 'info'
        if loss:
            message_type = 'error'
        em = make_embed(msg_type=message_type, title=title,
                        title_url=killmail_zkill)
        em.set_footer(icon_url=self.bot.user.avatar_url,
                      text="Provided Via firetail Bot + ZKill")
        em.set_thumbnail(url="https://image.eveonline.com/Type/{}_64.png".format(ship_lost_id))
        if victim_name is not None and victim_alliance is not None:
            em.add_field(name="Victim",
                         value="Name: [{}]({})\nCorp: [{}]({})\nAlliance: [{}]({})"
                         .format(victim_name,
                                 victim_zkill,
                                 victim_corp,
                                 victim_corp_zkill,
                                 victim_alliance,
                                 victim_alliance_zkill),
                         inline=False)
        elif victim_name is not None and victim_alliance is None:
            em.add_field(name="Victim",
                         value="Name: [{}]({})\nCorp: [{}]({})"
                         .format(victim_name,
                                 victim_zkill,
                                 victim_corp,
                                 victim_corp_zkill),
                         inline=False)
        elif victim_name is None and victim_alliance is not None:
            em.add_field(name="Kill Info",
                         value="Corp: [{}]({})\nAlliance: [{}]({})"
                         .format(victim_corp,
                                 victim_corp_zkill,
                                 victim_alliance,
                                 victim_alliance_zkill),
                         inline=False)
        elif victim_name is None and victim_alliance is None:
            em.add_field(name="Kill Info",
                         value="Corp: [{}]({})".format(victim_corp, victim_corp_zkill), inline=False)
        if final_blow_name is not None and final_blow_alliance is not None:
            em.add_field(name="Final Blow",
                         value="Name: [{}]({})\nShip: [{}]({})\nCorp: [{}]({})\nAlliance: [{}]({})"
                         .format(final_blow_name,
                                 final_blow_zkill,
                                 final_blow_ship,
                                 final_blow_ship_zkill,
                                 final_blow_corp,
                                 final_blow_corp_zkill,
                                 final_blow_alliance,
                                 final_blow_alliance_zkill),
                         inline=False)
        elif final_blow_name is not None and final_blow_alliance is None:
            em.add_field(name="Final Blow",
                         value="Name: [{}]({})\nShip: [{}]({})\nCorp: [{}]({})"
                         .format(final_blow_name,
                                 final_blow_zkill,
                                 final_blow_ship,
                                 final_blow_ship_zkill,
                                 final_blow_corp,
                                 final_blow_corp_zkill), inline=False)
        elif final_blow_name is None and final_blow_alliance is not None:
            em.add_field(name="Final Blow",
                         value="Structure: [{}]({})\nCorp: [{}]({})\nAlliance: [{}]({})"
                         .format(final_blow_ship,
                                 final_blow_ship_zkill,
                                 final_blow_corp,
                                 final_blow_corp_zkill,
                                 final_blow_alliance,
                                 final_blow_alliance_zkill),
                         inline=False)
        elif final_blow_name is False and final_blow_alliance is None:
            em.add_field(name="Final Blow",
                         value="Structure: [{}]({})\nCorp: [{}]({})"
                         .format(final_blow_ship,
                                 final_blow_ship_zkill,
                                 final_blow_corp,
                                 final_blow_corp_zkill),
                         inline=False)
        em.add_field(name="Details",
                     value='{}\nTime: {} EVE\nValue: {} ISK\nNearest Celestial: {}\n[zKill Link]({})'
                     .format(special_info,
                             kill_time,
                             value,
                             location_name,
                             killmail_zkill),
                     inline=False)
        channel = bot.get_channel(int(channel_id))
        try:
            return await channel.send(embed=em)
        except Exception:
            self.logger.exception(
                'Killmail - Killmail ID {} failed to send to channel {} due to..'.format(kill_id, channel_id))
            await self.remove_bad_channel(channel_id)

    async def request_data(self):
        base_url = "https://redisq.zkillboard.com"
        zkill = "{}/listen.php?queueID={}".format(base_url, self.bot.user.id)
        async with self.bot.session.get(zkill) as resp:
            data = await resp.text()
        try:
            data = json.loads(data)['package']
            if data.get('killID'):
                return data
        except Exception:
            return None

    async def remove_bad_channel(self, channel_id):
        sql = ''' DELETE FROM add_kills WHERE `channelid` = (?) '''
        values = (channel_id,)
        await db.execute_sql(sql, values)
        return self.logger.info('Killmail - Bad Channel {} removed successfully'.format(channel_id))
