from firetail.lib import db
from firetail.utils import make_embed
import time
import datetime
import asyncio
import json


class Notifications:
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
            config = self.config
            try:
                data = await self.request_data(config)
                if data is not None:
                    await self.process_data(data)
                else:
                    await asyncio.sleep(120)
                await asyncio.sleep(60)
            except Exception:
                self.logger.exception('ERROR:')
                await asyncio.sleep(120)

    async def process_data(self, data):
        sql = "SELECT value FROM firetail WHERE entry='newest_fleet_up'"
        stored_newest = await db.select(sql, True)
        if stored_newest is None:
            stored_newest = 0
        for operation in data:
            if int(stored_newest) < operation['Id']:
                sql = ''' REPLACE INTO firetail(entry,value) VALUES(?,?) '''
                values = ('newest_fleet_up', str(operation['Id']))
                await db.execute_sql(sql, values)
                await self.post_operation(operation, None)
                continue
            timestamp = time.mktime(datetime.datetime.strptime(
                operation['StartString'], "%Y-%m-%d %H:%M:%S").timetuple()) - 18000
            seconds_from_now = float(timestamp) - time.time()
            if 1800 > seconds_from_now > 0 and operation['Id'] not in self.soon_operations:
                self.soon_operations.append(operation['Id'])
                await self.post_operation(operation, False)
                continue
            if 300 > seconds_from_now > 0 and operation['Id'] not in self.very_soon_operations:
                self.very_soon_operations.append(operation['Id'])
                await self.post_operation(operation, True)
                continue

    async def post_operation(self, operation, very_soon):
        if very_soon:
            title = 'Fleet Starting In Less Than 5 Minutes'
        elif very_soon is None:
            title = 'New Fleet Posted'
        else:
            title = 'Fleet Starting In Less Than 30 Minutes'
        doctrine = 'N/A'
        if len(operation['Doctrines']) > 0:
            doctrine = operation['Doctrines']
        embed = make_embed(title=title, title_url='https://fleet-up.com/Operation#{}'.format(operation['Id']))
        embed.set_footer(icon_url=self.bot.user.avatar_url,
                         text="Provided Via Firetail Bot & Fleet-Up")
        embed.set_thumbnail(url="https://fleet-up.com/Content/Images/logo_title.png")
        embed.add_field(name="Fleet Information", value='Fleet Name: {}\nFleet Time: {} EVE\nPlanned Doctrines: {}\n'
                                                        'Form-Up Location: {} {}\nOrganizer: {}\n\nDetails: {}'.
                        format(operation['Subject'], operation['StartString'], doctrine,
                               operation['Location'], operation['LocationInfo'], operation['Organizer'],
                               operation['Details']))
        dest = self.bot.get_channel(int(self.config.fleetUp['channel_id']))
        await dest.send(embed=embed)

    async def request_data(self, config):
        base_url = "http://api.fleet-up.com/Api.svc/l5z6cq36hs7ojxHjk7GshvePY/"
        full_url = "{}{}/{}/Operations/{}".format(base_url, config.fleetUp['user_id'], config.fleetUp['api_code'],
                                                  config.fleetUp['group_id'])
        async with self.bot.session.get(full_url) as resp:
            data = await resp.text()
        try:
            data = json.loads(data)
            if data['Success']:
                return data['Data']
        except Exception:
            return None
