import os
import sys
import json

from pprint import pprint
from atexit import register
from datetime import datetime
from time import sleep
from src.hopbridge.variables import time_format
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.blockchain.evm import EvmContract


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)

# Fetch variables
info = json.loads(sys.argv[-1])
timestamp = datetime.now().astimezone().strftime(time_format)
print(f"{timestamp} - Started screening:\n")
pprint(info)

dictionaries = list(info.values())

# Create a contract instance only once and then query multiple times
evm_contracts = [EvmContract(item['network'], item['address']) for item in dictionaries]


while True:

    old_txns = [contract.get_last_txns(50) for contract in evm_contracts]

    # Wait for new transactions to appear
    sleep(10)

    new_txns = [contract.get_last_txns(50) for contract in evm_contracts]

    for num, item in enumerate(dictionaries):
        # If new txns found - check them and send the interesting ones
        found_txns = EvmContract.compare_lists(new_txns[num], old_txns[num])

        if len(found_txns) > 0:
            evm_contracts[num].alert_checked_txns(txns=found_txns,
                                                  min_txn_amount=item['min_amount'],
                                                  token_decimals=item['decimals'],
                                                  token_name=item['token'])
