from argparse import ArgumentParser

from src.hopbridge import __version__


# Create CLI interface
parser = ArgumentParser(
    usage="python3 %(prog)s <command> <input file>\n",
    description="Program that screens https://hop.exchange for arbitrage and etherscan for contract transactions. "
                "and alerts via a Telegram message."
                "Visit https://github.com/ivandimitrovkyulev/HopBridge for more info.",
    epilog=f"Version - {__version__}",
)

parser.add_argument(
    "-s", "--screen", action="store", type=str, nargs=1, metavar="\b", dest="screen",
    help=f"Screens for arbitrage opportunities between 2 tokens and notifies about the spot price "
         f"difference via a Telegram message.."
)

parser.add_argument(
    "-v", "--version", action="version", version=__version__,
    help="Prints the program's current version."
)

# Parse arguments
args = parser.parse_args()
