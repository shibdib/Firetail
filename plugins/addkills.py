from lib import esi
from lib import db


async def run(client, logger, config, message):
    # handle help request
    if len(message.content.split()) > 1:
        if message.content.split(' ', 1)[1].lower() == 'help':
            return await helptext(client, logger, config, message)
    else:
        return await client.send_message(message.channel, 'Not a valid group ID. Please use **!addKills help** for more info.')
    group = message.content.split(' ', 1)[1]
    channel = message.channel.id
    author = message.author.id
    server_owner = message.server.owner.id
    server = message.server.id
    group_corp = await esi.corporation_info(group)
    group_alliance = await esi.alliance_info(group)
    # Verify user requesting is the server owner
    if server_owner != author:
        return await client.send_message(message.channel, 'Only the server owner can perform this action.')
    # Check if this is a remove request
    if message.content.split(' ', 1)[1].lower() == 'remove':
        return await removeServer(client, message, logger, server)
    # Verify group exists
    if 'error' in group_corp and 'error' in group_alliance:
        return await client.send_message(message.channel, 'Not a valid group ID. Please use **!addKills help** for more info.')
    sql = ''' REPLACE INTO zkill(channelid,serverid,groupid,ownerid)
              VALUES(?,?,?,?) '''
    values = (channel, server, group, author)
    try:
        await db.execute_sql(logger, sql, values)
    except:
        return await client.send_message(message.channel, '**ERROR** - Failed to add the server. Contact the bot owner for assistance.')
    return await client.send_message(message.channel, '**Success** - This channel will begin receiving killmails as they occur.')


async def helptext(client, logger, config, message):
    msg = "This plugin allows you to designate a channel to receive killmails. While in the channel you'd like to use, " \
          "type **!addkills corp/allianceID** so for example to add TEST Alliance killmails it would be **!addkills " \
          "498125261**".format(message)
    logger.info('Price - ' + str(message.author) + ' requested help for this plugin')
    await client.send_message(message.channel, msg)


async def removeServer(client, message, logger, server):
    sql = ''' DELETE FROM zkill WHERE (serverid) = (?) '''
    values = server
    try:
        await db.execute_sql(logger, sql, values)
    except:
        return await client.send_message(message.channel, '**ERROR** - Failed to remove the server. Contact the bot owner for assistance.')
    return await client.send_message(message.channel, '**Success** - This bot will no longer report any killmails on this server.')
