"""Firetail - An EVE Online Discord Bot"""

import argparse
import asyncio
import sys

import discord

from firetail.core import bot, events
from firetail.utils import logger
from firetail.utils import ExitCodes

if discord.version_info.major < 1:
    print("You are not running discord.py v1.0.0a or above.\n\n"
          "firetail requires the new discord.py library to function "
          "correctly. Please install the correct version.")
    sys.exit(1)


def run_firetail(debug=None, launcher=None):
    firetail = bot.Firetail()
    events.init_events(firetail, launcher=launcher)
    firetail.logger = logger.init_logger(debug_flag=debug)
    firetail.load_extension('firetail.core.commands')
    firetail.load_extension('firetail.core.extension_manager')
    for ext in firetail.preload_ext:
        ext_name = ("firetail.extensions." + ext)
        firetail.load_extension(ext_name)
    loop = asyncio.get_event_loop()
    if firetail.token is None or not firetail.default_prefix:
        firetail.logger.critical("Token and prefix must be set in order to login.")
        sys.exit(1)
    try:
        loop.run_until_complete(firetail.start(firetail.token))
    except discord.LoginFailure:
        firetail.logger.critical("Invalid token")
        loop.run_until_complete(firetail.logout())
        firetail._shutdown_mode = ExitCodes.SHUTDOWN
    except KeyboardInterrupt:
        firetail.logger.info("Keyboard interrupt detected. Quitting...")
        loop.run_until_complete(firetail.logout())
        firetail._shutdown_mode = ExitCodes.SHUTDOWN
    except Exception as e:
        firetail.logger.critical("Fatal exception", exc_info=e)
        loop.run_until_complete(firetail.logout())
    finally:
        code = firetail._shutdown_mode
        sys.exit(code.value)


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="firetail - An EVE Online Discord Bot")
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")
    parser.add_argument(
        "--launcher", "-l", help=argparse.SUPPRESS, action="store_true")
    return parser.parse_args()


def main():
    args = parse_cli_args()
    run_firetail(debug=args.debug, launcher=args.launcher)


if __name__ == '__main__':
    main()
