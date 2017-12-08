from lib import db
from lib import esi
import discord


async def run(client, logger, config, message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    authstring = message.content.split()[1]
    characterid = await db.select_pending(authstring)
    corporationid = await esi.character_corp_id(characterid)
    allianceid = await esi.character_alliance_id(characterid)
    for authGroup in config["AUTH"]["AUTHGROUPS"]:
        if corporationid == authGroup["ID"] or allianceid == authGroup["ID"]:
            role = discord.utils.get(message.server.roles, name=config.auth.corprole)
            logger.info("User Authed")
            await client.add_roles(message.author, role)
            await client.send_message(message.channel, 'Auth Successful - Adding Role')
