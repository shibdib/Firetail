token = 'lol'  # Put the bot token from https://discordapp.com/developers/applications here
trigger = '!'  # the trigger for commands
nickname = 'Firetail'  # Name your bot
game = '!help for more info'  # What game the bot is playing

# Welcome Message
welcomeMessageEnabled = False  # Set to true if you'd like the message below to be sent to new users
welcomeMessage = '**Welcome to the server!**\n \nTo get roles type !auth to get a link to the authing system.\nIf you ' \
                 'want more information regarding other plugins type !help'

# Uncomment plugins to enable
# On Message Plugins
messagePlugins = (
    'eveTime',  # Get the time in eve and around the world
    'price',  # Price check plugin
)
forcePrivateMessage = False  # If true, all bot responses will be done via PM
deleteRequest = False  # If true, on bot response the message request is deleted (Works well with the above option)
# On Tick Plugins
tickPlugins = (
    #  'killmails'  #Killmail posting plugin
)

# Auto Responses - Add more with the format 'trigger': 'Auto response'
autoResponse = {
    'auth': 'To get roles on this server visit: ',
    'help': 'To get assistance with a plugin type !plugin help, currently active plugins are ' + str(messagePlugins)
}

# Killmail Plugin Settings
killmail = {  # add or remove groups as needed, groups must have unique names.
    'bigKills': True,  # Enable the sharing of eve wide big kills
    'bigKillsValue': 1000000000,  # Big kill ISK threshold
    'bigKillsChannel': '389827425581662226',  # Channel big kills are posted to
    'killmailGroups': {
        'group1': {  # feel free to add additional groups, be sure that each group has a unique name
            'id': '498125261',  # Corp/Alliance ID
            'channelId': '244061582496104448',  # Channel ID
            'lossMails': True  # Show Loss Mails
        }
    }
}
