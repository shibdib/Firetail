async def run(client, config, message):
    for plugin in config.messageplugins:
        if plugin:
            await plugin.run(client, message)
