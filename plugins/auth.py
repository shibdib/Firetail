from lib import db
from lib import esi
from config import config
import discord


async def run(client, logger, message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    authstring = message.content.split()[1]
    characterid = await db.select_pending(authstring)
    corporationid = await esi.character_corp_id(characterid)
    if corporationid == config.auth.corpid:
        role = discord.utils.get(message.server.roles, name=config.auth.corprole)
        await client.add_roles(message.author, role)
        await client.send_message(message.channel, 'Auth Successful - Adding Corp Role')
