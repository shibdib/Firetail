# bot token from discord developers
# go to https://discordapp.com/developers/applications/me and create an application
# make it a bot user
# put the bot user token below
bot_token = ''

# default bot settings
bot_prefix = ['!']
bot_master = 174764205927432192  # The discord ID of the owner
bot_coowners = [114428861990699012]  # The discord ID's of co-owners

# minimum required permissions for bot (Only really needed if you're inviting it to other servers, probably safe to
# not touch this)
bot_permissions = 1571904

# Add any extensions to the below preload_extentions array to always load them on restart. Note that extensions can be
# loaded on demand using the !ext load command.
preload_extensions = [
    # 'killmails',  # Killmail posting extension
    # 'add_kills',  # Enables the addkills command
    'eve_time',  # Get the time in eve and around the world
    'eve_status',  # Get the status of the server and the player count
    'price',  # Price check extension
    'group_lookup',  # Get corp/alliance info
    'char_lookup',  # Get character info
    'jump_planner',  # Provides the shortcut for dotlan jump planning
    'jump_range',  # Provides the shortcut for dotlan jump range
    'location_scout',  # Provides intel on systems/constellations/regions
    # 'sov_tracker',  # Provides real time info on sov fights
    # 'fleet_up',  # Shares upcoming fleet-up operations
    # The following plugins are still in testing, use at your own risk
    # 'stream_player',  # Play youtube and other streams in a voice channel
    # 'jabber_relay'  # Completely broken, dont use me yet
]

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

# Fleet-Up Plugin Settings
fleetUp = {  # add or remove groups as needed, groups must have unique names.
    'group_id': 12345,  # Fleet-up group ID
    'user_id': 12345,  # User ID from your fleet-up api-key
    'api_code': '',  # API Code from your fleet-up api-key
    'channel_id': 12345,  # Channel to post fleet-up operations
}

