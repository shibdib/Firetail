import sys
import argparse
import subprocess


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Firetail - An EVE Online Discord Bot")
    parser.add_argument(
        "--no-restart", "-r",
        help="Disables auto-restart.", action="store_true")
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")
    return parser.parse_known_args()


def main():
    print('''
  ______ _          _        _ _  \n
 |  ____(_)        | |      (_) | \n
 | |__   _ _ __ ___| |_ __ _ _| | \n
 |  __| | | '__/ _ \ __/ _` | | | \n
 | |    | | | |  __/ || (_| | | | \n
 |_|    |_|_|  \___|\__\__,_|_|_| \n
                                 ''')

    if sys.version_info < (3, 5, 0):
        print("ERROR: Minimum Python version not met.\n"
              "Firetail requires Python 3.5 or higher.\n")
        return

    print("Launching Firetail...", end=' ', flush=True)

    launch_args, ft_args = parse_cli_args()

    if launch_args.debug:
        ft_args.append('-d')

    ft_args.append('-l')

    while True:
        code = subprocess.call(["firetail-bot", *ft_args])
        if code == 0:
            print("Goodbye!")
            break
        elif code == 26:
            print("Rebooting! I'll be back in a bit!\n")
            continue
        else:
            if launch_args.no_restart:
                break
            print("I crashed! Trying to restart...\n")
    print("Exit code: {exit_code}".format(exit_code=code))
    sys.exit(code)
