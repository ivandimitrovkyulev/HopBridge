import os
import sys
import json

from tqdm import tqdm
from copy import deepcopy
from pprint import pprint
from atexit import register
from datetime import datetime
from time import sleep, perf_counter

from src.hopbridge.blockchain.interface import args
from src.hopbridge.variables import time_format
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.blockchain.evm import EvmContract


if len(sys.argv) != 3:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} <mode> contracts.json\n")

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)

# Fetch variables
info = json.loads(sys.argv[-1])
timestamp = datetime.now().astimezone().strftime(time_format)
print(f"{timestamp} - Started screening:\n")

dictionaries = [dictionary for dictionary in info.values() if type(dictionary) is dict]
pprint(dictionaries)

# Create a contract instance only once and then query multiple times
print("Initialising contracts...")
evm_contracts = [EvmContract(item['network'], item['bridge_address']) for item in tqdm(dictionaries)]


if args.transactions:
    print("Screening for 'Transactions'...")

    old_txns = [contract.get_last_txns(100) for contract in evm_contracts]
    while True:
        # Wait for new transactions to appear
        sleep(10)

        new_txns = [contract.get_last_txns(100) for contract in evm_contracts]

        for num, item in enumerate(dictionaries):
            if len(new_txns[num]) == 0 or len(new_txns[num]) == 0:
                continue

            # If new txns found - check them and send the interesting ones
            found_txns = EvmContract.compare_lists(new_txns[num], old_txns[num])

            if len(found_txns) > 0:
                evm_contracts[num].alert_checked_txns(txns=found_txns,
                                                      min_txn_amount=item['min_amount'],
                                                      token_decimals=item['decimals'],
                                                      token_name=item['token'])

        # Save latest txns in old_txns
        old_txns = deepcopy(new_txns)


if args.erc20tokentxns:
    print("Screening for 'Erc20 Token Txns'...")

    filter_by = tuple(info['filter_by'])

    old_txns = [contract.get_last_erc20_txns(item['token_address'], 100, filter_by=filter_by)
                for contract, item in zip(evm_contracts, dictionaries)]

    while True:
        # Wait for new transactions to appear
        sleep(10)

        new_txns = [contract.get_last_erc20_txns(item['token_address'], 100, filter_by=filter_by)
                    for contract, item in zip(evm_contracts, dictionaries)]

        for num, item in enumerate(dictionaries):
            if len(new_txns[num]) == 0 or len(new_txns[num]) == 0:
                continue

            # If new txns found - check them and send the interesting ones
            found_txns = EvmContract.compare_lists(new_txns[num], old_txns[num])

            if len(found_txns) > 0:
                evm_contracts[num].alert_erc20_txns(txns=found_txns, min_txn_amount=item['min_amount'])

        # Save latest txns in old_txns
        old_txns = deepcopy(new_txns)
