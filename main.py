import os
import sys
import json

from time import sleep
from datetime import datetime
from itertools import product
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.common.exceptions import exit_handler_driver
from src.hopbridge.web.price_query import query_hop
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")


# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler_driver, chrome_driver, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

tokens = ("USDC", "DAI", "USDT")
networks = ("polygon", "gnosis", "optimism", "arbitrum")

pairs = list(product(tokens, networks))

info_dict = json.loads(sys.argv[-1])
min_arb = info_dict['min_arb']
in_network = info_dict['in_network']

args = [(chrome_driver, info_dict[pair[0]], min_arb, in_network, pair[1], pair[0]) for pair in pairs]

terminal_msg = ""
for item in pairs:
    terminal_msg += f"{item[0]}, {in_network} --> {item[1]}\n"

print(f"{timestamp}\n"
      f"Started screening https://app.hop.exchange with the following on the following networks:\n"
      f"{terminal_msg}")

while True:
    for arg in args:
        query_hop(*arg)

    sleep(info_dict['sleep_time'])
