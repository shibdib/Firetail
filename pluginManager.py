import importlib


async def message_plugin(client, logger, config, message):
    command = message.content.split()[0][len(config.trigger):].lower()
    if command in config.messagePlugins:
        plugin = importlib.import_module("plugins/" + command)
        await plugin.run(client, logger, config, message)


async def tick_plugin(client, logger, config, message):
    for plugin in config.tickPlugins:
        await plugin.run(client, logger, config, message)
