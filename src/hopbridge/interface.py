from argparse import ArgumentParser

from src.arbscreener import __version__


# Create CLI interface
parser = ArgumentParser(
    usage="python3 %(prog)s [-d] [SCHEMA]\n",
    description="Screener that looks for arbitrage opportunities between 2 tokens and notifies about the spot price "
                "difference via a Telegram message. "
                "Visit https://github.com/ivandimitrovkyulev/ArbScreener for more info.",
    epilog=f"Version - {__version__}",
)

parser.add_argument(
    "-s", "--screen", action="store", type=str, nargs=1, metavar="\b", dest="screen",
    help=f"Screens for arbitrage opportunities between 2 tokens and notifies about the spot price "
         f"difference via a Telegram message.."
)

parser.add_argument(
    "-d", "--debug", action="store", type=bool, nargs=1, metavar="\b", dest="debug",
    help=f"Runs the script in debug mode and prints all queries to terminal only."
)

parser.add_argument(
    "-v", "--version", action="version", version=__version__,
    help="Prints the program's current version."
)

# Parse arguments
args = parser.parse_args()
