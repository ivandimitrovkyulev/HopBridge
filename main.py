import os
import sys
import json

from time import sleep, perf_counter
from datetime import datetime
from itertools import product
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.common.exceptions import exit_handler_driver
from src.hopbridge.web.price_query import query_hop
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

info = json.loads(sys.argv[-1])

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler_driver, chrome_driver, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

tokens = tuple(token for token in info.keys() if token != 'settings')
networks = ("polygon", "gnosis", "optimism", "arbitrum")
in_network = "ethereum"
sleep_time = info['settings']['sleep_time']

pairs = list(product(tokens, networks))

args = [(chrome_driver, info[pair[0]], in_network, pair[1], pair[0], len(tokens))
        for pair in pairs]

msg = ""
for pair in pairs:
    data = info[pair[0]]
    msg += f"Arb {data['min_arb']} {pair[0]}, " \
           f"range {[i for i in range(data['start'], data['end'], data['step'])]}, " \
           f"{in_network} --> {pair[1]}\n"
print(f"{timestamp}\nStarted screening https://app.hop.exchange with the following networks:\n{msg}")

while True:
    start = perf_counter()

    for arg in args:
        query_hop(*arg)

    sleep(sleep_time)

    end = perf_counter()

    print(end - start)
