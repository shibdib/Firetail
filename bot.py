import discord
import asyncio
import logging
from config import config
from plugins import onMessage
from plugins import onTick

logger = logging.getLogger('firetail')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='logs/firetail.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()


@client.event
async def on_message(message):
    if message.content.startswith(config.trigger):
        await onMessage.run(client, config, message)


@client.event
async def on_ready():
    logger.info('------')
    logger.info('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')


client.run(config.token)
