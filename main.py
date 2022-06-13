import os
import sys
import json

from time import sleep
from datetime import datetime
from itertools import product
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.exceptions import exit_handler_driver
from src.hopbridge.price_query import query_hop
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit("Usage: python3 main.py input.json\n")


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

info_dict = json.loads(sys.argv[-1])
sleep_time = info_dict['sleep_time']
eth_range = info_dict['eth_range']
eth_min_arb = info_dict['eth_min_arb']
stb_range = info_dict['stb_range']
stb_min_arb = info_dict['stb_min_arb']


args_eth = [(chrome_driver, eth_range, eth_min_arb, in_ntwrk, comb[1], comb[0]) for comb in combs_eth]
args_stb = [(chrome_driver, stb_range, stb_min_arb, in_ntwrk, comb[1], comb[0]) for comb in combs_stb]
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
