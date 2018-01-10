from firetail.lib import db
from firetail.core import checks
from discord.ext import commands


class AddKills:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='addkills')
    @checks.is_mod()
    async def _add_kills(self, ctx):
        """Do '!addkills groupID' to get killmails in the channel.
        Do '!addkills big' to get EVE Wide big kills reported in the channel.
        Do '!addkills remove' to stop receiving killmails in the channel."""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help addkills** for more info.')
        # Check if server is at cap
        sql = "SELECT id FROM add_kills WHERE serverid = {}".format(ctx.message.guild.id)
        current_requests = await db.select(sql)
        if len(current_requests) >= 5 and ctx.message.content.split(' ', 1)[1].lower() != 'remove':
            return await ctx.channel.send("You've reached the limit for adding killmail channels to your server")
        if len(ctx.message.content.split()) == 1:
            return await ctx.channel.send('Not a valid group ID. Please use **!help addkills** '
                                          'for more info.')
        group = ctx.message.content.split(' ', 1)[1]
        if group.lower().strip() == 'big':
            group = 9
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        server = ctx.message.guild.id
        group_corp = await self.bot.esi_data.corporation_info(group)
        group_alliance = await self.bot.esi_data.alliance_info(group)
        # Check if this is a remove request
        if ctx.message.content.split(' ', 1)[1].lower() == 'remove':
            return await self.remove_server(ctx)
        # Verify group exists
        if 'error' in group_corp and 'error' in group_alliance and group != 9:
            return await ctx.channel.send('Not a valid group ID. Please use **!help addkills** '
                                          'for more info.')
        try:
            name = group_corp['name']
        except Exception:
            if group != 9:
                name = group_alliance['name']
            else:
                name = 'EVE Wide 2b+ Kills'
        sql = ''' REPLACE INTO add_kills(channelid,serverid,groupid,ownerid)
                  VALUES(?,?,?,?) '''
        values = (channel, server, group, author)
        await db.execute_sql(sql, values)
        self.logger.info('addkills - ' + str(ctx.message.author) + ' added killmail tracking to their server.')
        return await ctx.channel.send('**Success** - This channel will begin receiving killmails for {} '
                                      'as they occur.'.format(name))

    async def remove_server(self, ctx):
        sql = ''' DELETE FROM add_kills WHERE `channelid` = (?) '''
        values = (ctx.message.channel.id,)
        try:
            await db.execute_sql(sql, values)
        except Exception:
            return await ctx.channel.send('**ERROR** - Failed to remove killmails. Contact the bot'
                                          ' owner for assistance.')
        self.logger.info('addkills - ' + str(ctx.message.author) + ' removed killmail tracking from a channel.')
        return await ctx.channel.send('**Success** - This bot will no longer report any killmails for this channel.')

    @_add_kills.error
    async def _add_kills_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.channel.send('Only channel moderators can do that.')
