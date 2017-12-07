from plugins import onMessage_test


async def run(client, message):
    await onMessage_test.plugin(client, message)
