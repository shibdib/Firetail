from plugins import onMessage_test


async def run(client, config, message):
    if config.test:
        await onMessage_test.plugin(client, message)
