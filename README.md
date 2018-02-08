# Firetail
[![Discord Bots](https://discordbots.org/api/widget/389952638327717928.svg)](https://discordbots.org/bot/389952638327717928)

An EVE Online Discord Bot (Continuation of Dramiel)


[Invite the public bot today!](https://discordapp.com/oauth2/authorize?client_id=389952638327717928&scope=bot&permissions=0)


[To discuss.](https://discord.gg/ZWmzTP3)


# Ideas
Please use the issues feature here to make requests for what you want in the bot that is not already listed below.

# Planned Features
- Ping Relaying (Is this still really needed?)
- Fleetup Integration
- Notifications/In-Game Mails

# Possible Features

# Docker
To run Firetail with docker - you need a few things
1. You need to install Docker (Docker-CE)
2. You need to install Docker-Compose (pip3 install docker-compose)

Once those are sorted, you need to copy the config (cp firetail/example_config.py firetail/config.py) and edit it.
Then `docker-compose up` to test run it (It auto attaches) - and once everything looks fine - you simply do: `docker-compose start` and the bot will now run (Should even do so through a reboot, or a crash)