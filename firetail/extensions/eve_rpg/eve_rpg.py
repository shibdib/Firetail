from discord.ext import commands
from firetail.lib import db
from firetail.core import checks
import asyncio


class EveRpg:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.config = bot.config
        self.logger = bot.logger
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    @commands.command(name='setRpg')
    @checks.is_admin()
    async def _rpg(self, ctx):
        """Sets a channel as an RPG channel.
        Do **!setRpg** to have a channel relay all RPG events.
        The RPG includes players from all servers this instance of the bot is on."""
        sql = ''' REPLACE INTO eve_rpg_channels(server_id,channel_id,owner_id)
                  VALUES(?,?,?) '''
        author = ctx.message.author.id
        channel = ctx.message.channel.id
        server = ctx.message.guild.id
        values = (server, channel, author)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rpg - {} added {} to the rpg channel list.')
        return await ctx.author.send('**Success** - Channel added.')

    @commands.command(name='rpg')
    @checks.spam_check()
    @checks.is_whitelist()
    async def _rpg(self, ctx):
        """Sign up for the RPG.
        If your server doesn't have an RPG channel have an admin do **!setRpg** to receive the game events."""
        sql = ''' REPLACE INTO eve_rpg_players(server_id,player_id)
                  VALUES(?,?) '''
        author = ctx.message.author.id
        server = ctx.message.guild.id
        values = (server, author)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rpg - ' + str(ctx.message.author) + ' added to the game.')
        return await ctx.author.send('**Success** - Welcome to the game.')

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.process_turn()
                await asyncio.sleep(25)
            except Exception:
                self.logger.exception('ERROR:')
                await asyncio.sleep(5)

    async def process_turn(self):
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY RAND() LIMIT 1 '''
        player = await db.select(sql)
        user = self.bot.get_user(int(player[2]))
        if user is None:
            self.logger.exception('eve_rpg - Bad player attempted removing....')
            return await self.remove_bad_user(player[2])
        #  Share turn
        sql = "SELECT * FROM eve_rpg_channels"
        game_channels = await db.select(sql)
        for channels in game_channels:
            channel = self.bot.get_channel(int(channels[2]))
            if channel is None:
                self.logger.exception('eve_rpg - Bad Channel Attempted removing....')
                await self.remove_bad_channel(channels[2])
            channel.send('Testing RPG **{}** died to rats'.format(user['display_name']))

    async def remove_bad_user(self, channel_id):
        sql = ''' DELETE FROM eve_rpg_players WHERE `player_id` = (?) '''
        values = (channel_id,)
        await db.execute_sql(sql, values)
        return self.logger.info('eve_rpg - Bad player removed successfully')

    async def remove_bad_channel(self, channel_id):
        sql = ''' DELETE FROM eve_rpg_channels WHERE `channel_id` = (?) '''
        values = (channel_id,)
        await db.execute_sql(sql, values)
        return self.logger.info('eve_rpg - Bad Channel removed successfully')
