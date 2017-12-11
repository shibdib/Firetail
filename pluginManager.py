import importlib.util


async def message_plugin(client, logger, config, message):
    command = message.content.split()[0][len(config.trigger):].lower()
    if command in config.messagePlugins:
        spec = importlib.util.spec_from_file_location(command, "plugins/" + command + ".py")
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        if message.content.split()[1] == 'help':
            await plugin.helpText(client, logger, config, message)
        else:
            await plugin.run(client, logger, config, message)

    if command in config.autoResponse:
        msg = config.autoResponse[command].format(message)
        await client.send_message(message.channel, msg)


async def tick_plugin(client, logger, config, message):
    for plugin in config.tickPlugins:
        await plugin.run(client, logger, config, message)
