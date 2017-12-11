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
tickPlugins = [
]

# Auto Responses
autoResponse = {
    'auth': 'To get roles on this server visit: ' + authUrl,
    'help': 'To get assistance with a plugin type !plugin help, currently active plugins are ' + str(messagePlugins)
}