import os
import sys
import json

from pprint import pprint
from atexit import register
from datetime import datetime
from time import (
    sleep,
    perf_counter,
)
from src.hopbridge.variables import time_format
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.blockchain.evm import (
    EvmContract,
    Network,
)


if len(sys.argv) != 2:
    sys.exit(f"Usage: python3 {os.path.basename(__file__)} contracts.json\n")

# Send telegram debug message if program terminates
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)
timestamp = datetime.now().astimezone().strftime(time_format)

# Fetch variables
info = json.loads(sys.argv[-1])
print(f"{timestamp} - Started screening:\n")
pprint(info)

dictionaries = [info[name] for name in info]

# Create a contract instance only once and then query multiple times
evm_contracts = [EvmContract(Network(item['network'])) for item in dictionaries]

to_txns = [contract.get_last_txns(item['address'], 1)[-1]['to']
           for contract, item in zip(evm_contracts, dictionaries)]

contract_instances = [contract.create_contract(to_txn)
                      for contract, to_txn in zip(evm_contracts, to_txns)]


while True:
    start_time = perf_counter()

    old_txns = [contract.get_last_txns(item['address'], 50)
                for contract, item in zip(evm_contracts, dictionaries)]

    # Wait for new transactions to appear
    sleep(5)

    new_txns = [contract.get_last_txns(item['address'], 50)
                for contract, item in zip(evm_contracts, dictionaries)]

    for num, item in enumerate(dictionaries):
        # If new txns found - check them and send the interesting ones
        found_txns = EvmContract.compare_lists(new_txns[num], old_txns[num])

        evm_contracts[num].alert_checked_txns(txns=found_txns,
                                              min_txn_amount=item['min_amount'],
                                              contract_instance=contract_instances[num],
                                              token_decimals=item['decimals'],
                                              token_name=item['token'])

    end_time = perf_counter()
    print(f"Loop finished in {end_time - start_time} secs.")
