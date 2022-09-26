import os
import sys
import json
import asyncio

from copy import deepcopy
from atexit import register
from datetime import datetime
from time import (
    sleep,
    perf_counter,
)
from concurrent.futures import ThreadPoolExecutor

from src.hopbridge.blockchain.interface import args
from src.hopbridge.blockchain.evm import EvmContract
from src.hopbridge.blockchain.helpers import (
    print_start_message,
    gather_funcs,
)
from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.variables import time_format


if len(sys.argv) != 3:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} <mode> contracts.json\n")

# Send telegram debug message if program terminates
timestamp = datetime.now().astimezone().strftime(time_format)
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)

# Fetch variables
info = json.loads(sys.argv[-1])
bridges = [bridge for bridge in info['bridges'].values()]

print(f"{timestamp} - Started screening:\n")
print_start_message(bridges)

# Create a contract instance only once and then query multiple times
arguments = [[item['network'], item['bridge_address']] for item in bridges]

with ThreadPoolExecutor(max_workers=len(bridges)) as pool:
    results = pool.map(lambda p: EvmContract(*p), arguments, timeout=20)

evm_contracts = list(results)
contract_instances = [contract for contract in evm_contracts if contract.contract]
print(f"Initialised {len(contract_instances)}/{len(bridges)} contract instances. Look at log files for more details.")


if args.transactions:
    print("Screening for 'Transactions'...")

    old_txns = [contract.get_last_txns(100) for contract in evm_contracts]

    while True:
        # Wait for new transactions to appear
        sleep(10)

        new_txns = [contract.get_last_txns(100) for contract in evm_contracts]

        for i, item in enumerate(bridges):

            # If empty list returned - no point to compare
            if len(new_txns[i]) == 0 or len(old_txns[i]) == 0:
                continue

            # If new txns found - check them and send the interesting ones
            found_txns = EvmContract.compare_lists(new_txns[i], old_txns[i])

            if len(found_txns) > 0:
                evm_contracts[i].alert_checked_txns(txns=found_txns,
                                                    min_txn_amount=item['min_amount'],
                                                    token_decimals=item['decimals'],
                                                    token_name=item['token'])

        # Save latest txns in old_txns
        old_txns = deepcopy(new_txns)


if args.erc20tokentxns:
    telegram_send_message(f"✅ HOP_ETHERSCAN has started.")

    filter_by = tuple(info['settings']['filter_by'])
    sleep_time = info['settings']['sleep_time']
    print(f"Screening for 'Erc20 Token Txns' and filtering by {filter_by}:")

    txn_args = [[item['token_address'], 100, filter_by] for contract, item in zip(evm_contracts, bridges)]
    txn_funcs = [contract.get_last_erc20_txns for contract in evm_contracts]

    old_txns = asyncio.run(gather_funcs(txn_funcs, txn_args))

    loop_counter = 1
    while True:
        # Wait for new transactions to appear
        start = perf_counter()
        sleep(sleep_time)

        new_txns = asyncio.run(gather_funcs(txn_funcs, txn_args))

        for i, item in enumerate(bridges):

            # If empty list returned - no point to compare
            if not new_txns[i]:
                continue

            # If new txns found - check them and send the interesting ones
            found_txns = EvmContract.compare_lists(new_txns[i], old_txns[i])

            if found_txns:
                evm_contracts[i].alert_erc20_txns(txns=found_txns, min_txn_amount=item['min_amount'])

                # Save latest txns in old_txns only if there is a found txn
                old_txns[i] = deepcopy(new_txns[i])

        timestamp = datetime.now().astimezone().strftime(time_format)
        print(f"{timestamp} - Loop {loop_counter} executed in {(perf_counter() - start):,.2f} secs.")
        loop_counter += 1
