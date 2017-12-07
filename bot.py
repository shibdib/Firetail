import discord
import asyncio

firetail = discord.Client()

@firetail.event
async def on_ready():
    print('Logged in as')
    print(firetail.user.name)
    print(firetail.user.id)
    print('------')\

@firetail.event
async def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0.mention} to {1.name}!'
    await firetail.send_message(server, fmt.format(member, server))

@firetail.event
async def on_message(message):
    if message.content.startswith('!test'):
        counter = 0
        tmp = await firetail.send_message(message.channel, 'Calculating messages...')
        async for log in firetail.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await firetail.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await firetail.send_message(message.channel, 'Done sleeping')

@firetail.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == firetail.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await firetail.send_message(message.channel, msg)

async def my_background_task():
    await firetail.wait_until_ready()
    counter = 0
    channel = discord.Object(id='channel_id_here')
    while not firetail.is_closed:
        counter += 1
        await firetail.send_message(channel, counter)
        await asyncio.sleep(60) # task runs every 60 seconds

@firetail.event
async def on_ready():
    print('Logged in as')
    print(firetail.user.name)
    print(firetail.user.id)
    print('------')

firetail.loop.create_task(my_background_task())

firetail.run('token')