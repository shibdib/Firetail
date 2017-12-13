import discord
import pytz
from datetime import datetime


async def run(client, logger, config, message):
    # handle help request
    if len(message.content.split()) > 1:
        if message.content.split(' ', 1)[1].lower() == 'help':
            await helptext(client, logger, config, message)
            return
    eve_time = datetime.utcnow().strftime('%H:%M')
    est = datetime.now(pytz.timezone("America/New_York")).strftime('%H:%M')
    pst = datetime.now(pytz.timezone("America/Los_Angeles")).strftime('%H:%M')
    cet = datetime.now(pytz.timezone("Europe/Copenhagen")).strftime('%H:%M')
    msk = datetime.now(pytz.timezone("Europe/Moscow")).strftime('%H:%M')
    aest = datetime.now(pytz.timezone("Australia/Sydney")).strftime('%H:%M')
    em = discord.Embed()
    em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot")
    em.add_field(name="Time Zones",
                 value="**EVE Time ** \n**PST/California ** \n**EST/New York ** \n**CET/Copenhagen ** \n**MSK/Moscow ** \n**AEST/Sydney **", inline=True)
    em.add_field(name="Time",
                 value=eve_time + " \n" + pst + " \n" + est + " \n" + cet + " \n" + msk + " \n" + aest, inline=True)
    logger.info('Time - ' + str(message.author) + ' requested time info')
    await client.send_message(message.channel, embed=em)


async def helptext(client, logger, config, message):
    msg = "To use this plugin simply do **!time**".format(message)
    logger.info('Time - ' + str(message.author) + ' requested help for this plugin')
    await client.send_message(message.channel, msg)
