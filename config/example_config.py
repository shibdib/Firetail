# Put the bot token from https://discordapp.com/developers/applications here
token = 'Mzg4MzEwNDczODAxNDY1ODU3.DQzRyg.YkMZxzWStqiPiO8qm8HswuzBqjg'
trigger = '!'
authUrl = 'http://keepstar.shibdib.info'

# Welcome Message
welcomeMessageEnabled = False  # Set to true if you'd like the message below to be sent to new users
welcomeMessage = '**Welcome to the server!**\n \nTo get roles type !auth to get a link to the authing system.\nIf you ' \
                 'want more information regarding other plugins type !help'
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
