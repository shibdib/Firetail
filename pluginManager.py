

async def message_plugin(client, logger, config, message):
    for plugin in config.messagePlugins:
        await plugin.run(client, logger, config, message)


async def tick_plugin(client, logger, config, message):
    for plugin in config.tickPlugins:
        await plugin.run(client, logger, config, message)
