import os
import sys
import json

from time import sleep, perf_counter
from datetime import datetime
from atexit import register

from src.hopbridge.driver.driver import chrome_driver
from src.hopbridge.web.helpers import print_start_message
from src.hopbridge.web.price_query import query_hop
from src.hopbridge.common.exceptions import exit_handler_driver
from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.variables import time_format


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler_driver, chrome_driver, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

# Extract input info from file
info = json.loads(sys.argv[-1])

sleep_time, special_chat = info['settings'].values()

args = []
for coin in info['coins']:
    for in_network in info['coins'][coin]['in_networks']:
        for out_network in info['coins'][coin]['out_networks']:
            # Append argument for each network configuration
            args.append((chrome_driver, info['coins'][coin], in_network, out_network, coin, special_chat))


print(f"{timestamp} - Started screening https://app.hop.exchange with the following networks:")
print_start_message(args)

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
