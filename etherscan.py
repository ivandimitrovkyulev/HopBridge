import os
import sys
import json

from pprint import pprint
from time import sleep
from atexit import register
from datetime import datetime

from src.hopbridge.variables import time_format
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.blockchain.evm import (
    Txns,
    EvmContract,
)


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

# Fetch variables
info = json.loads(sys.argv[-1])

addresses = [info[contract_name]['address'] for contract_name in info]
dictionaries = [info[contract_name] for contract_name in info]


# Create a contract instance only once and then query multiple times
contract_instances = [EvmContract.create_contract(Txns.get_last_txns(address, 1)[-1]['to'])
                      for address in addresses]

print(f"{timestamp} - Started screening:\n")
pprint(info)

while True:

    old_txns = [Txns.get_last_txns(address, 50) for address in addresses]

    # Wait for new transactions to appear
    sleep(5)

    new_txns = [Txns.get_last_txns(address, 50) for address in addresses]

    for num, dictionary in enumerate(dictionaries):
        # If new txns found - check them and send the interesting ones
        found_txns = Txns.compare_lists(new_txns[num], old_txns[num])
        Txns.alert_checked_txns(found_txns,
                                min_txn_amount=dictionary['min_amount'],
                                contract_instance=contract_instances[num],
                                token_decimals=dictionary['decimals'],
                                token_name=dictionary['token'],
                                network_name=dictionary['network'])
