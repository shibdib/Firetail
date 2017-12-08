
# Put the bot token from https://discordapp.com/developers/applications here
token = 'token'
trigger = '!'

# Uncomment plugins to enable
# On Message Plugins
messagePlugins = [
    'auth',
    #  'price',
    #  'char'
]
# On Tick Plugins
tickPlugins = [
]


# Auth Setup
class auth(object):
    corpid = 1000066
    corprole = 'Name'