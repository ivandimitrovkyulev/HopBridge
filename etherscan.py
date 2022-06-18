import os
import sys
import json

from pprint import pprint
from time import sleep
from atexit import register
from datetime import datetime

from src.hopbridge.variables import time_format
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.blockchain.evm import EvmContract


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

dictionaries = [info[name] for name in info if type(info[name]) == dict]

# Create a contract instance only once and then query multiple times
networks = {name: EvmContract(name) for name in info['networks']}
contracts = {item['network']: networks[item['network']].get_last_txns(item['address'], 1)[-1]['to']
             for item in dictionaries}


while True:

    old_txns = [networks[item['network']].get_last_txns(item['address'], 50)
                for item in dictionaries]

    # Wait for new transactions to appear
    sleep(5)

    new_txns = [networks[item['network']].get_last_txns(item['address'], 50)
                for item in dictionaries]

    for num, item in enumerate(dictionaries):
        # If new txns found - check them and send the interesting ones
        found_txns = EvmContract.compare_lists(new_txns[num], old_txns[num])
        networks[item['network']].alert_checked_txns(txns=found_txns,
                                                     contract_instance=contracts[item['network']],
                                                     min_txn_amount=item['min_amount'],
                                                     token_decimals=item['decimals'],
                                                     token_name=item['token'],
                                                     network_name=item['network'])
