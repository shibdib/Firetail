import discord
from config import config
from plugins import onMessage
from plugins import onTick

client = discord.Client()


@client.event
async def on_message(message):
    onMessage.run(client, message)


@client.event
async def on_ready():
    print('------')
    print('Firetail - Created by Shibdib https://github.com/shibdib/Firetail')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


client.run(config.token)
