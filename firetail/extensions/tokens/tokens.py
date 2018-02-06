from discord.ext import commands
from firetail.lib import db
from firetail.core import checks
import time
import asyncio
import base64


class Token:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.config = bot.config
        self.logger = bot.logger
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    @commands.command(name='token')
    @checks.spam_check()
    async def _token(self, ctx):
        token = ctx.message.content.split(' ', 1)
        auth = base64.b64encode(bytes(':'.join([self.config.tokens['client_id'], self.config.tokens['secret']]),
                                      'utf-8'))
        access_token = await self.bot.esi_data.refresh_access_token(token, auth)
        try:
            verify = await self.bot.esi_data.verify_token(access_token['access_token'])
            character_id = verify['CharacterID']
        except:
            return await ctx.send("ERROR: That is not a valid refresh token.")
        expires = float(access_token['expires_in']) + time.time()
        sql = ''' REPLACE INTO access_tokens(character_id,discord_id,refresh_token,access_token,expires)
                  VALUES(?,?,?,?,?) '''
        values = (character_id, ctx.author.id, token, access_token['access_token'], expires)
        await db.execute_sql(sql, values)
        self.logger.info('Token - ' + str(ctx.message.author) + ' added a refresh token.')
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()
            await ctx.send("{.author.mention} refresh token added.".format(ctx))
        elif ctx.guild is not None:
            await ctx.send("{.author.mention} refresh token added. I do not have the roles required to delete your"
                           "your message, so for your security please delete the token submission".format(ctx))
        else:
            await ctx.send("{.author.mention} refresh token added.".format(ctx))

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.refresh()
                await asyncio.sleep(1260)
            except Exception:
                self.logger.exception('ERROR:')
                await asyncio.sleep(1260)

    async def refresh(self):
        auth = base64.b64encode(bytes(':'.join([self.config.tokens['client_id'], self.config.tokens['secret']]),
                                      'utf-8'))
        sql = "SELECT * FROM access_tokens"
        tokens = await db.select(sql)
        for token in tokens:
            access_token = await self.bot.esi_data.refresh_access_token(token[3], auth)
            try:
                verify = await self.bot.esi_data.verify_token(access_token['access_token'])
                character_id = verify['CharacterID']
            except:
                sql = ''' DELETE FROM access_tokens WHERE refresh_token = ? '''
                values = (access_token['refresh_token'])
                await db.execute_sql(sql, values)
                continue
            expires = float(access_token['expires_in']) + time.time()
            sql = ''' REPLACE INTO access_tokens(refresh_token,access_token,expires)
                      VALUES(?,?,?) '''
            values = (token[3], access_token['access_token'], expires)
            await db.execute_sql(sql, values)
