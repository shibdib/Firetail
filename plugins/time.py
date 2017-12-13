import discord
import pytz
from datetime import datetime, timezone


async def run(client, logger, config, message):
    utc_dt = datetime(2002, 10, 27, 6, 0, 0, tzinfo=utc)
    eve_time = pytz.timezone("UTC")
    est = pytz.timezone("America/New_Yorkg")
    pst = pytz.timezone("America/Los_Angeles")
    cet = pytz.timezone("Europe/Copenhagen")
    msk = pytz.timezone("Europe/Moscow")
    eve_time = pytz.timezone("Australia/Sydney")
    datetime_without_tz = datetime.datetime.strptime("2015-02-14 12:34:56", "%Y-%m-%d %H:%M:%S")
    datetime_with_tz = local_tz.localize(datetime_without_tz, is_dst=None)  # No daylight saving time
    datetime_in_utc = datetime_with_tz.astimezone(pytz.utc)

    str1 = datetime_without_tz.strftime('%Y-%m-%d %H:%M:%S %Z')
    str2 = datetime_with_tz.strftime('%Y-%m-%d %H:%M:%S %Z')
    str3 = datetime_in_utc.strftime('%Y-%m-%d %H:%M:%S %Z')
    em = discord.Embed(title=item.title(), description="Price information from Jita 4-4",
                       url="https://market.fuzzwork.co.uk/type/" + str(typeid) + "/", colour=0xDEADBF)
    em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + Fuzzwork Market")
    em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(typeid) + "_64.png")
    em.add_field(name="Buy", value="Low: " + buymin + " \nAvg: " + buyavg + " \nHigh: " + buymax + " \n ", inline=True)
    em.add_field(name="Sell", value="Low: " + sellmin + " \nAvg: " + sellavg + " \nHigh: " + sellmax + " \n ",
                 inline=True)
    await client.send_message(message.channel, embed=em)


async def helptext(client, logger, config, message):
    msg = "To use this plugin simply do **!time**".format(message)
    await client.send_message(message.channel, msg)
