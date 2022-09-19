import os
import sys
import json
import time

from time import perf_counter
from atexit import register
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.hopbridge.blockchain.evm import EvmContract
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.evm_scanner.helpers import (
    check_arb,
    print_start_message,
)
from src.hopbridge.variables import (
    time_format,
    ankr_endpoints,
)


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} scan_contracts.json\n")

# Send telegram debug message if program terminates
timestamp = datetime.now().astimezone().strftime(time_format)
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)

info = json.loads(sys.argv[-1])
sleep_time = info['settings']['sleep_time']
network_data = info['network_data'].values()

evm_args = [[item['network'], item['address'], ankr_endpoints[item['network'].lower()]]
            for item in network_data]

# Create a contract instance only once and then query multiple times
with ThreadPoolExecutor(max_workers=len(evm_args)) as pool:
    results = pool.map(lambda p: EvmContract(*p), evm_args, timeout=10)
bridge_contracts = list(results)

arb_args = [[contract, arg['swap_amount'], arg['coin'], arg['min_arb']]
            for contract, arg in zip(bridge_contracts, network_data)]

print(f"{timestamp} - Started screening:\n")
print_start_message(arb_args)

loop_counter = 1
while True:
    start = perf_counter()

    with ThreadPoolExecutor(max_workers=len(arb_args)) as pool:
        results = pool.map(lambda p: check_arb(*p), arb_args, timeout=10)

    time.sleep(sleep_time)

    timestamp = datetime.now().astimezone().strftime(time_format)
    print(f"{timestamp} - Loop {loop_counter} executed in {(perf_counter() - start):,.2f} secs.")
    loop_counter += 1
