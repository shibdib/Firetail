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
        """Do '!addkills ID' to get all killmails in the channel.
        Do '!addkills ID false' to not receive losses.
        Do '!addkills ID 1000000' to not receive kills of value less than the number.
        Do '!addkills ID 1000000 false' to not receive kills of value less than the number and no losses.
        Do '!addkills big' to get EVE Wide big kills reported in the channel.
        Do '!addkills big 10000000000' to get EVE Wide big kills greater than the number reported in the channel.
        Do '!addkills remove' to stop receiving killmails in the channel.

        ID can be an Alliance ID, Corp ID, Region ID, System ID (Use Zkill or Dotlan to get them)"""
        threshold = 2000000000
        losses = 'true'
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help addkills** for more info.')
        # Check if server is at cap
        sql = "SELECT id FROM add_kills WHERE serverid = {}".format(ctx.message.guild.id)
        current_requests = await db.select(sql)
        if len(current_requests) >= 5 and ctx.message.content.split(' ')[1].lower() != 'remove':
            return await ctx.channel.send("You've reached the limit for adding killmail channels to your server")
        if len(ctx.message.content.split()) == 1:
            return await ctx.channel.send('Not a valid ID. Please use **!help addkills** '
                                          'for more info.')
        group = ctx.message.content.split(' ')[1]
        if group.lower().strip() == 'big':
            group = 9
        else:
            threshold = 1
        try:
            second = ctx.message.content.split(' ')[2]
            if second.isdigit():
                threshold = second
            if second.lower() == 'true' or second.lower() == 'false':
                losses = second
            try:
                third = ctx.message.content.split(' ')[3]
                if third.isdigit():
                    threshold = third
                if third.lower() == 'true' or third.lower() == 'false':
                    losses = third.lower()
            except IndexError:
                None
        except IndexError:
            losses = 'true'
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        server = ctx.message.guild.id
        clean = '{0:,.2f}'.format(float(threshold))
        group_corp = await self.bot.esi_data.corporation_info(group)
        group_alliance = await self.bot.esi_data.alliance_info(group)
        solar_system = await self.bot.esi_data.system_info(group)
        region = await self.bot.esi_data.region_info(group)
        loss = ''
        if losses == 'true':
            loss = ' and lossmails'
        # Check if this is a remove request
        if ctx.message.content.split(' ', 1)[1].lower() == 'remove':
            return await self.remove_server(ctx)
        # Verify group exists
        if 'error' in group_corp and 'error' in group_alliance and 'error' in solar_system and 'error'\
                in region and group != 9:
            return await ctx.channel.send('Not a valid ID. Please use **!help addkills** '
                                          'for more info.')
        name = '**Unable to get name**'
        if 'error' not in group_corp:
            name = group_corp['name']
        elif 'error' not in group_alliance:
            name = group_alliance['name']
        elif 'error' not in solar_system:
            name = solar_system['name']
        elif 'error' not in region:
            name = region['name']
        if group == 9:
            name = 'EVE Wide {}+ Kills'.format(clean)
        sql = ''' REPLACE INTO add_kills(channelid,serverid,losses,threshold,groupid,ownerid)
                  VALUES(?,?,?,?,?,?) '''
        values = (channel, server, losses, threshold, group, author)
        await db.execute_sql(sql, values)
        self.logger.info('addkills - ' + str(ctx.message.author) + ' added killmail tracking to their server.')
        return await ctx.channel.send('**Success** - This channel will begin receiving killmails{} for {} when the value'
                                      ' is greater than {} ISK as they occur.'.format(loss, name, clean))

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
