from plugins import onMessage_test


async def run(client, message):
    onMessage_test.plugin(client, message)
