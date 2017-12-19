from firetail.lib import db
from discord.ext import commands


class AddKills:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='addkills')
    async def _add_kills(self, ctx):
        """Do '!addkills groupID' to get killmails in the channel.
        Do '!addkills remove' to stop receiving killmails."""
        # handle help request
        if len(ctx.message.content.split()) == 1:
            return await ctx.channel.send('Not a valid group ID. Please use **!help addkills** '
                                          'for more info.')
        group = ctx.message.content.split(' ', 1)[1]
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        server_owner = ctx.message.guild.owner.id
        server = ctx.message.guild.id
        group_corp = await self.bot.esi_data.corporation_info(group)
        group_alliance = await self.bot.esi_data.alliance_info(group)
        # Verify user requesting is the server owner
        if server_owner != author:
            return await ctx.channel.send('Only the server owner can perform this action.')
        # Check if this is a remove request
        if ctx.message.content.split(' ', 1)[1].lower() == 'remove':
            return await self.removeServer(ctx)
        # Verify group exists
        if 'error' in group_corp and 'error' in group_alliance:
            return await ctx.channel.send('Not a valid group ID. Please use **!help addkills** '
                                          'for more info.')
        sql = ''' REPLACE INTO zkill(channelid,serverid,groupid,ownerid)
                  VALUES(?,?,?,?) '''
        values = (channel, server, group, author)
        await db.execute_sql(sql, values)
        self.logger.info('addkills - ' + str(ctx.message.author) + ' added killmail tracking to their server.')
        return await ctx.channel.send('**Success** - This channel will begin receiving killmails '
                                      'as they occur.')

    async def removeServer(self, ctx):
        sql = ''' DELETE FROM zkill WHERE `serverid` = (?) '''
        values = (ctx.message.guild.id,)
        try:
            await db.execute_sql(sql, values)
        except:
            return await ctx.channel.send('**ERROR** - Failed to remove the server. Contact the bot'
                                          ' owner for assistance.')
        self.logger.info('addkills - ' + str(ctx.message.author) + ' removed killmail tracking from their server.')
        return await ctx.channel.send('**Success** - This bot will no longer report any killmails on this server.')
