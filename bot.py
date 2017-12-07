import discord
import logging
from config import config
import pluginManager

logger = logging.getLogger('firetail')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='logs/firetail.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()

logger.info('Loading Message Plugins: ')
for plugin in config.messagePlugins:
    logger.info(plugin)
logger.info('------')

logger.info('Loading Tick Plugins: ')
for plugin in config.tickPlugins:
    logger.info(plugin)
logger.info('------')


@client.event
async def on_message(message):
    if message.content.startswith(config.trigger):
        await pluginManager.message_plugin(client, logger, config, message)


@client.event
async def on_ready():
    logger.info('------')
    logger.info('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')


client.run(config.token)
