import discord
import logging
import json
import pluginManager

with open('config/config.json', 'r') as f:
    config = json.load(f)

logger = logging.getLogger('firetail')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='logs/firetail.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = discord.Client()

logger.info('Loading Message Plugins: ')
for plugin in config["ENABLED_PLUGINS"]["ON_MESSAGE"]:
    logger.info(plugin)
logger.info('------')

logger.info('Loading Tick Plugins: ')
for plugin in config["ENABLED_PLUGINS"]["ON_TICK"]:
    logger.info(plugin)
logger.info('------')


@client.event
async def on_message(message):
    if message.content.startswith(config["BOT"]["TRIGGER"]) and message.content.split(' ', 1)[0][1:] in config["ENABLED_PLUGINS"]["ON_MESSAGE"]:
        await pluginManager.message_plugin(client, logger, config, message)


@client.event
async def on_ready():
    logger.info('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')


client.run(config["BOT"]["TOKEN"])
