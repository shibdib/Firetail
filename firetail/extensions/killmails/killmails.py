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
                self.logger.info('ERROR:', exc_info=True)
                await asyncio.sleep(5)

    async def process_data(self, kill_data):
        config = self.config
        km_groups = config.killmail['killmailGroups']
        big_kills = config.killmail['bigKills']
        big_kills_value = config.killmail['bigKillsValue']
        #  Foreach thru all provided groups
        for group in km_groups:
            killmail_group_id = int(config.killmail['killmailGroups'][group]['id'])
            channel_id = config.killmail['killmailGroups'][group]['channelId']
            loss = config.killmail['killmailGroups'][group]['lossMails']
            #  Skip npc
            if kill_data['zkb']['npc'] or not kill_data['killmail']['victim']['corporation_id']:
                break
            #  Get all group id's from the mail
            group_ids = []
            if loss:
                group_ids.append(int(kill_data['killmail']['victim']['corporation_id']))
                if 'alliance_id' in kill_data['killmail']['victim']:
                    group_ids.append(int(kill_data['killmail']['victim']['alliance_id']))
            for attacker in kill_data['killmail']['attackers']:
                if 'corporation_id' in attacker:
                    group_ids.append(int(attacker['corporation_id']))
                if 'alliance_id' in attacker:
                    group_ids.append(int(attacker['alliance_id']))
            if killmail_group_id in group_ids:
                await self.process_kill(channel_id, kill_data)
            for ext in self.bot.extensions:
                if 'add_kills' in ext:
                    sql = "SELECT * FROM add_kills"
                    other_channels = await db.select(sql)
                    for add_kills in other_channels:
                        if add_kills[3] in group_ids:
                            await self.process_kill(add_kills[1], kill_data)
                        if add_kills[3] == 9 and kill_data['zkb']['totalValue'] >= big_kills_value:
                            await self.process_kill(add_kills[1], kill_data, True)
            if kill_data['zkb']['totalValue'] >= big_kills_value and big_kills:
                channel_id = config.killmail['bigKillsChannel']
                await self.process_kill(channel_id, kill_data, True)

    async def process_kill(self, channel_id, kill_data, big=False):
        bot = self.bot
        kill_id = kill_data['killID']
        kill_time = kill_data['killmail']['killmail_time'].split('T', 1)[1][:-4]
        value_raw = kill_data['zkb']['totalValue']
        value = '{0:,.2f}'.format(float(value_raw))
        try:
            victim_id = kill_data['killmail']['victim']['character_id']
            victim_name = await self.bot.esi_data.character_name(victim_id)
        except Exception:
            victim_name = None
        ship_lost_id = kill_data['killmail']['victim']['ship_type_id']
        ship_lost_raw = await self.bot.esi_data.type_info_search(ship_lost_id)
        ship_lost = ship_lost_raw['name']
        victim_corp_id = kill_data['killmail']['victim']['corporation_id']
        victim_corp_raw = await self.bot.esi_data.corporation_info(victim_corp_id)
        victim_corp = victim_corp_raw['name']
        try:
            victim_alliance_id = kill_data['killmail']['victim']['alliance_id']
            victim_alliance_raw = await self.bot.esi_data.alliance_info(victim_alliance_id)
            victim_alliance = victim_alliance_raw['name']
        except Exception:
            victim_alliance = None
        solar_system_id = kill_data['killmail']['solar_system_id']
        solar_system_info = await self.bot.esi_data.system_info(solar_system_id)
        solar_system_name = solar_system_info['name']
        if '-' in solar_system_name:
            solar_system_name = solar_system_name.upper()
        title = ship_lost + " Destroyed in "
        if big:
            title = "BIG KILL REPORTED: " + ship_lost + " Destroyed in "
        em = make_embed(msg_type='info', title=title.title() + str(solar_system_name),
                        title_url="https://zkillboard.com/kill/" + str(kill_id) + "/",
                        content='Killed At: ' + kill_time + ' EVE')
        em.set_footer(icon_url=self.bot.user.avatar_url,
                      text="Provided Via firetail Bot + ZKill")
        em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(ship_lost_id) + "_64.png")
        if victim_name is not None and victim_alliance is not None:
            em.add_field(name="Victim",
                         value="Name: " + str(victim_name) + "\nShip Value: " + value + " \nCorp: " + str(victim_corp) +
                               " \nAlliance: " + str(victim_alliance) + " \n ")
        elif victim_name is not None and victim_alliance is None:
            em.add_field(name="Victim",
                         value="Name: " + str(victim_name) + "\nShip Value: " + value + " \nCorp: " + str(victim_corp))
        elif victim_name is None and victim_alliance is not None:
            em.add_field(name="Structure Info",
                         value="Structure Value: " + value + "\nCorp: " + str(victim_corp) + " \nAlliance: " +
                               str(victim_alliance) + " \n ")
        elif victim_name is None and victim_alliance is None:
            em.add_field(name="Structure Info",
                         value="Structure Value: " + value + "\nCorp: " + str(victim_corp))
        try:
            channel = bot.get_channel(int(channel_id))
            channel_name = channel.name
        except Exception:
            self.logger.info('Killmail - Bad Channel Attempted {} removing'.format(channel_id))
            return await self.remove_bad_channel(channel_id)
        self.logger.info(('Killmail - Kill # {} has been posted to {}'
                          '').format(kill_id, channel_name))
        try:
            return await channel.send(embed=em)
        except Exception:
            return self.logger.info('Killmail - Message failed to send to channel {} due to {}'.format(channel_id, Exception))

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
        return self.logger.info('Killmail - Bad Channel removed successfully')
