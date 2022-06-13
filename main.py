import os
import sys

from time import sleep
from datetime import datetime
from itertools import product
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.exceptions import exit_handler_driver
from src.hopbridge.price_query import query_hop
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit("Usage: python3 main.py <time to sleep in secs>\n")

sleep_time = int(sys.argv[-1])

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler_driver, chrome_driver, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

tokens_stb = ("USDC", "DAI", "USDT")
tokens_eth = ("ETH", )
networks = ("polygon", "gnosis", "optimism", "arbitrum")
in_ntwrk = "ethereum"

combs_eth = list(product(tokens_eth, networks))
combs_stb = list(product(tokens_stb, networks))

args_eth = [(chrome_driver, (5, 55, 5), 0.03, in_ntwrk, comb[1], comb[0]) for comb in combs_eth]
args_stb = [(chrome_driver, (10000, 110000, 10000), 20, in_ntwrk, comb[1], comb[0]) for comb in combs_stb]
args = args_eth + args_stb

terminal_msg = ""
for item in combs_eth + combs_stb:
    terminal_msg += f"{item[0]}, {in_ntwrk} --> {item[1]}\n"

print(f"{timestamp}\n"
      f"Started screening https://app.hop.exchange with the following on the following networks:\n"
      f"{terminal_msg}")

while True:
    for arg in args:
        query_hop(*arg)

    sleep(sleep_time)
