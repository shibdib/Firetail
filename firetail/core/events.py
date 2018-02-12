import datetime
import logging
import traceback
import aiohttp

from discord.ext import commands
from firetail import config

import firetail

INTRO = ("====================================\n"
         "firetail - An EVE Online Discord Bot\n"
         "====================================\n")

log = logging.getLogger("firetail")


def init_events(bot, launcher=None):
    @bot.event
    async def on_connect():
        if hasattr(bot, 'launch_time'):
            print("Reconnected.")

    @bot.event
    async def on_ready():
        if not hasattr(bot, 'launch_time'):
            bot.launch_time = datetime.datetime.utcnow()
        if not launcher:
            print(INTRO)
        print("We're on!\n")
        guilds = len(bot.guilds)
        users = len(list(bot.get_all_members()))
        print("Version: {}\n".format(firetail.__version__))
        if guilds:
            print("Servers: {}".format(guilds))
            print("Members: {}".format(users))
        else:
            print("I'm not in any server yet, so be sure to invite me!")
        if bot.invite_url:
            print("\nInvite URL: {}\n".format(bot.invite_url))
            try:
                db_token = config.db_token
                url = "https://discordbots.org/api/bots/{}/stats".format(bot.user.id)
                headers = {"Authorization": db_token}
                payload = {"server_count": len(bot.guilds)}
                async with aiohttp.ClientSession() as client:
                    await client.post(url, data=payload, headers=headers)
            except:
                return

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.BadArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("That command is disabled.")
        elif isinstance(error, commands.CheckFailure):
            pass
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("That command is not available in DMs.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown. "
                           "Try again in {:.2f}s"
                           "".format(error.retry_after))
        elif isinstance(error, commands.CommandInvokeError):
            # Need to test if the following still works
            """
            no_dms = "Cannot send messages to this user"
            is_help_cmd = ctx.command.qualified_name == "help"
            is_forbidden = isinstance(error.original, discord.Forbidden)
            if is_help_cmd and is_forbidden and error.original.text == no_dms:
                msg = ("I couldn't send the help message to you in DM. Either"
                       " you blocked me or you disabled DMs in this server.")
                await ctx.send(msg)
                return
            """
            log.exception("Exception in command '{}'"
                          "".format(ctx.command.qualified_name),
                          exc_info=error.original)
            message = ("Error in command '{}'. Check your console or "
                       "logs for details."
                       "".format(ctx.command.qualified_name))
            exception_log = ("Exception in command '{}'\n"
                             "".format(ctx.command.qualified_name))
            exception_log += "".join(traceback.format_exception(
                type(error), error, error.__traceback__))
            bot._last_exception = exception_log
            if "Missing Permissions" in exception_log:
                await ctx.author.send("**ERROR:** The Bot Does Not Have All Required Permissions In That Channel.")
            else:
                await ctx.send(message)

        else:
            log.exception(type(error).__name__, exc_info=error)

    @bot.event
    async def on_message(message):
        bot.counter["messages_read"] += 1
        await bot.process_commands(message)

    @bot.event
    async def on_resumed():
        bot.counter["sessions_resumed"] += 1

    @bot.event
    async def on_command(command):
        if 'help' in command.message.content.lower() and command.guild is not None:
            await command.send("{.author.mention} check your DM's for the help info.".format(command))
        bot.counter["processed_commands"] += 1

    @bot.event
    async def on_guild_join(guild):
        log.info("Connected to a new guild. Guild ID/Name: {}/{}".format(str(guild.id), guild.name))
        try:
            db_token = config.db_token
            url = "https://discordbots.org/api/bots/{}/stats".format(bot.user.id)
            headers = {"Authorization": db_token}
            payload = {"server_count": len(bot.guilds)}
            async with aiohttp.ClientSession() as client:
                await client.post(url, data=payload, headers=headers)
        except:
            return

    @bot.event
    async def on_guild_remove(guild):
        log.info("Leaving guild. Guild ID/Name: {}/{}".format(str(guild.id), guild.name))
        try:
            db_token = config.db_token
            url = "https://discordbots.org/api/bots/{}/stats".format(bot.user.id)
            headers = {"Authorization": db_token}
            payload = {"server_count": len(bot.guilds)}
            async with aiohttp.ClientSession() as client:
                await client.post(url, data=payload, headers=headers)
        except:
            return

    @bot.event
    async def on_member_ban(guild, user):
        log.info("New Ban Reported. Guild ID/Name: {}/{} -- Member ID/Name: {}/{}".format(str(guild.id), guild.name,
                                                                                          str(user.id), user.name))

    @bot.event
    async def on_member_join(member):
        if config.enable_welcome is True:
            member.send(config.welcome_string)
