from plugins import auth


async def message_plugin(client, logger, config, message):
    if message.content.split(' ', 1)[0][1:] == 'auth':
        await auth.run(client, logger, message)


async def tick_plugin(client, logger, config, message):
    for plugin in config.tickPlugins:
        await plugin.run(client, message)
