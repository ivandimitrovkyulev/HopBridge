import os

from time import (
    sleep,
    perf_counter,
)
from copy import deepcopy
from datetime import datetime
from atexit import register

from src.hopbridge.blockchain.evm import EvmContract
from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.common.exceptions import exit_handler
from src.hopbridge.variables import time_format


# Send telegram debug message if program terminates
timestamp = datetime.now().astimezone().strftime(time_format)
program_name = os.path.abspath(os.path.basename(__file__))
register(exit_handler, program_name)

address = '0x2468603819Bf09Ed3Fb6f3EFeff24B1955f3CDE1'
network = 'ethereum'
txn_count = 20

print(f"Started screening {address} on {network}.\n")

contract = EvmContract(network, address)

old_txns = contract.get_last_txns(txn_count)

loop_counter = 1
while True:

    start = perf_counter()
    sleep(10)

    new_txns = contract.get_last_txns(txn_count)

    if len(new_txns) == 0:
        continue

    last_txn_hash = new_txns[0]['hash']

    found_txns = EvmContract.compare_lists(new_txns, old_txns)

    # Only if txn is new
    if found_txns:

        for found_txn in found_txns:
            txn_hash = found_txn['hash']

            link = f"https://etherscan.io/tx/{txn_hash}"
            message = "New transaction on Aurora Rainbow Bridge!"

            telegram_message = f"<a href='{link}'>{message}</a>"
            telegram_send_message(message, telegram_chat_id='-678782541')
            print(f"{message}: {link}")

        old_txns = deepcopy(new_txns)

    timestamp = datetime.now().astimezone().strftime(time_format)
    print(f"{timestamp} - Loop {loop_counter} executed in {(perf_counter() - start):,.2f} secs. "
          f"Last txn hash: {last_txn_hash}")
    loop_counter += 1
