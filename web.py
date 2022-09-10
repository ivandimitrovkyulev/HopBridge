import os
import sys
import json

from time import sleep, perf_counter
from datetime import datetime
from itertools import product
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.common.exceptions import exit_handler_driver
from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.web.price_query import query_hop
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

info = json.loads(sys.argv[-1])

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler_driver, chrome_driver, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

tokens = tuple(token for token in info['coins'].keys())
out_networks = ("polygon", "gnosis", "optimism", "arbitrum")
in_network = "ethereum"
sleep_time = info['settings']['sleep_time']
special_chat = info['settings']['special_chat']

token_netw_pairs = list(product(tokens, out_networks))

args = [(chrome_driver, info['coins'][token], in_network, out_network, token, special_chat)
        for token, out_network in token_netw_pairs]

network_msgs = []
for i, pair in enumerate(token_netw_pairs):
    token, out_network = pair
    ranges, arb, decimal = info['coins'][token].values()
    network_msgs.append(f"{i+1}. Min_arb: {arb} {token}, range{[i for i in range(*ranges)]}, "
                        f"{in_network} -> {out_network}\n")

print(f"{timestamp} - Started screening https://app.hop.exchange with the following networks:")
print("".join(network_msgs))

telegram_send_message(f"✅ HOP_WEB has started.")

while True:
    start = perf_counter()

    token = args[0][4]
    for arg in args:
        # Refresh only if token changes
        if token != arg[4]:
            # Refresh this way! and update token
            chrome_driver.get("https://www.google.com")
            token = arg[4]

        # Query https://app.hop.exchange for prices
        query_hop(*arg)

    # Refresh this way! one more time to prepare for new while loop
    chrome_driver.get("https://www.google.com")

    # Sleep and print loop info
    sleep(sleep_time)
    timestamp = datetime.now().astimezone().strftime(time_format)
    print(f"{timestamp} - Loop executed in {perf_counter() - start} secs.")
