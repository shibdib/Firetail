# Put the bot token from https://discordapp.com/developers/applications here
token = 'Mzg4MzEwNDczODAxNDY1ODU3.DQzRyg.YkMZxzWStqiPiO8qm8HswuzBqjg'
trigger = '!'
authUrl = 'http://keepstar.shibdib.info'

# Uncomment plugins to enable
# On Message Plugins
messagePlugins = (
    'test',
    'price',
    #  'char'
)
# On Tick Plugins
tickPlugins = (
    #  'killmails'
)

# Auto Responses
autoResponse = {
    'auth': 'To get roles on this server visit: ' + authUrl,
    'help': 'To get assistance with a plugin type !plugin help, currently active plugins are ' + str(messagePlugins)
}


# Killmail Plugin Settings
killmail = {  # add or remove groups as needed, groups must have unique names.
    'bigKills': True,
    'bigKillsValue': 1000000000,
    'bigKillsChannel': '389827425581662226',
    'killmailGroups': {
        'group1': {
            'id': '498125261',  # Corp/Alliance ID
            'channelId': '244061582496104448',  # Channel ID
            'lossMails': True  # Show Loss Mails
        }
    }
}


# Jabber Relayings
jabber = {  # add or remove groups as needed, groups must have unique names.
    'username': 'bot@test.com',
    'password': 'password',
    'triggers': {
        'trigger1': {
            'string': 'To All Online',
            'Channel': '389865784656134155'
        }
    }
}