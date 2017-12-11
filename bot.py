import discord
import logging
import pluginManager
import asyncio
from config import config

logger = logging.getLogger('firetail')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='logs/firetail.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()
logger.info(' -------INITIATING STARTUP------- ')

logger.info('Loading Message Plugins: ')
for plugin in config.messagePlugins:
    logger.info(plugin)
logger.info('------')

logger.info('Loading Tick Plugins: ')
for plugin in config.tickPlugins:
    logger.info(plugin)
logger.info('------')


# Tick Loop
async def tick_loop():
    await client.wait_until_ready()
    while not client.is_closed:
        await pluginManager.tick_plugin(client, logger, config)
        await asyncio.sleep(3)  # task runs every 60 seconds


@client.event
async def on_message(message):
    if message.content.startswith(config.trigger):
        await pluginManager.message_plugin(client, logger, config, message)


@client.event
async def on_ready():
    logger.info('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    logger.info('Logged in as: ' + client.user.name)
    logger.info('------')


client.loop.create_task(tick_loop())
client.run(config.token)
