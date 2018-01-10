# bot token from discord developers
bot_token = ''

# default bot settings
bot_prefix = ['!']
bot_master = 174764205927432192
bot_coowners = [114428861990699012]

# minimum required permissions for bot
# bot_permissions = 268822608

# 'killmails' - Killmail posting extension
# 'eveTime' - Get the time in eve and around the world
# 'price' - Price check extension
# 'eve_status' - Get TQ Status
# 'group_lookup' - Get corp/alliance info
# 'char_lookup' - Get character info

preload_extensions = ['eve_time', 'price', 'eve_status', 'group_lookup', 'char_lookup']

game = '!help for more info'
dm_only = False  # bot responses always sent via direct message
delete_commands = False  # user commands are deleted automatically

# Welcome message for new users
enable_welcome = False
welcome_string = ('**Welcome to the server!**\n \nTo get roles type !auth to '
                  'get a link to the authing system.\nIf you want more '
                  'information regarding other plugins type !help')


# Auto Responses - Add more with the format 'trigger': 'Auto response'
auto_responses = {
    'auth': 'To get roles on this server visit: '
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
