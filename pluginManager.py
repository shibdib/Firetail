import importlib.util


async def message_plugin(client, logger, config, message):
    command = message.content.split()[0][len(config.trigger):].lower()
    if command in config.messagePlugins:
        spec = importlib.util.spec_from_file_location(command, "plugins/" + command + ".py")
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        await plugin.run(client, logger, config, message)


async def tick_plugin(client, logger, config, message):
    for plugin in config.tickPlugins:
        await plugin.run(client, logger, config, message)
