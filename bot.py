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
    await onMessage.run(client, config, message)


@client.event
async def on_ready():
    print('------')
    print('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


client.run(config.token)
