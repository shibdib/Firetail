import discord
import logging
from logging.handlers import RotatingFileHandler
import sys
import pluginManager
import asyncio
from config import config

logger = logging.getLogger('firetail')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(filename='logs/firetail.log', encoding='utf-8', maxBytes=5*1024*1024, backupCount=10)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


async def my_handler(type, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))


sys.excepthook = my_handler


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
        await asyncio.sleep(3)  # task runs every 3 seconds


@client.event
async def on_message(message):
    if message.content.startswith(config.trigger):
        await pluginManager.message_plugin(client, logger, config, message)


@client.event
async def on_member_join(member):
    if config.welcomeMessageEnabled:
        await client.send_message(member, config.welcomeMessage)


@client.event
async def on_server_join(server):
    if config.welcomeMessageEnabled:
        logger.info('Connected to Server: ' + server.id)


@client.event
async def on_server_remove(server):
    if config.welcomeMessageEnabled:
        logger.info('Left Server: ' + server.id)


@client.event
async def on_ready():
    logger.info('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    logger.info('Logged in as: ' + client.user.name)
    logger.info('------')
    # Set playing
    await client.change_presence(game=discord.Game(name=config.game))


client.loop.create_task(tick_loop())
client.run(config.token)
