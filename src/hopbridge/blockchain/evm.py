import os
import json
import requests

from datetime import datetime
from typing import List, Dict

from web3 import Web3
from web3.contract import Contract

from src.hopbridge.common.logger import (
    log_txns,
    log_error,
)
from src.hopbridge.variables import time_format
from src.hopbridge.common.message import telegram_send_message


class EvmContract:
    """
    EVM contract and transaction screener class.
    """
    def __init__(self, name: str, address: str):

        networks = {'arbitrum': ['https://api.arbiscan.io', 'https://arbiscan.io'],
                    'optimism': ['https://api-optimistic.etherscan.io', 'https://optimistic.etherscan.io']}
        if name.lower() not in networks:
            raise ValueError(f"No such network. Choose from: {networks}")

        self.name = name.lower()
        self.address = address.lower()
        self.network = networks[self.name][1]

        self.node_api_key = os.getenv(f"{self.name}_API_KEY")

        self.abi_endpoint = f"{networks[self.name][0]}/api?module=contract&action=getabi" \
                            "&address={txn_to}" \
                            f"&apikey={self.node_api_key}"

        self.url = f"{networks[self.name][0]}/api?module=account&action=txlist" \
                   "&address={address}&startblock=0&endblock=99999999&sort=desc" \
                   f"&apikey={self.node_api_key}"

        self.message = "{time_stamp}\n" \
                       "{txn_amount:,} {token_name} swapped on " \
                       "<a href='{network}/tx/{txn_hash}'>{name}</a>"

        # Create contract instance
        to_txn = self.get_last_txns(1, self.address)[-1]['to']
        self.contract_instance = self.create_contract(to_txn)

    def create_contract(self, txn_to: str) -> Contract:
        """
        Creates a contract instance ready to be interacted with.

        :param txn_to: Transaction 'to' address
        :return: web3 Contract instance
        """
        # Contract's ABI
        abi_endpoint = self.abi_endpoint.format(txn_to=txn_to)

        project_id = os.getenv("PROJECT_ID")
        infura_url = f"https://mainnet.infura.io/v3/{project_id}"
        w3 = Web3(Web3.HTTPProvider(infura_url))

        # Convert transaction address to check-sum address
        checksum_address = Web3.toChecksumAddress(txn_to)

        abi = json.loads(requests.get(abi_endpoint).text)

        # Create contract instance
        contract = w3.eth.contract(address=checksum_address, abi=abi['result'])

        return contract

    @staticmethod
    def run_contract(contract: Contract, txn_input: str) -> dict:
        """
        Runs an EVM contract given a transaction input.

        :param contract: web3 Contract instance
        :param txn_input: Transaction input field
        :return: Dictionary of transaction output
        """

        # Get transaction output from contract instance
        _, func_params = contract.decode_function_input(txn_input)

        return func_params

    @staticmethod
    def compare_lists(new_list: List[Dict[str, str]], old_list: List[Dict[str, str]],
                      keyword: str = 'hash') -> list:
        """
        Compares two lists of dictionaries.

        :param new_list: New list
        :param old_list: Old list
        :param keyword: Keyword to compare with
        :return: List of dictionaries that are in new list but not in old list
        """
        list_diff = []

        try:
            hashes = []
            for txn in old_list:
                hashes.append(txn[keyword])

            for txn in new_list:
                if txn[keyword] not in hashes:
                    list_diff.append(txn)
        except TypeError:
            return []

        return list_diff

    def get_last_txns(self, txn_count: int = 1, address: str = "") -> List:
        """
        Gets the last transactions from a specified contract address.

        :param txn_count: Number of transactions to return
        :param address: Contract address
        :return: A list of transaction dictionaries
        """
        if txn_count < 1:
            txn_count = 1

        if address == "":
            address = self.address

        url = self.url.format(address=address)

        try:
            txn_dict = requests.get(url).json()

            # Get a list with number of txns
            last_transactions = txn_dict['result'][:txn_count]

            return last_transactions

        except Exception:
            log_error.warning("Error in function 'get_last_txns': Unable to fetch transaction data.")
            return []

    def alert_checked_txns(self, txns: list, min_txn_amount: float,
                           token_decimals: int, token_name: str) -> None:
        """
        Checks transaction list and alerts if new transaction is important.

        :param txns: List of transactions
        :param min_txn_amount: Minimum transfer amount to alert for
        :param token_decimals: Number of decimals for this coin being swapped
        :param token_name: Name of token
        :return: None
        """

        for txn in txns:
            # Simulate contract execution and calculate amount
            contract_output = EvmContract.run_contract(self.contract_instance, txn['input'])
            txn_amount = float(contract_output['amount']) / (10 ** token_decimals)

            if token_decimals >= 6:
                txn_amount = round(txn_amount, int(token_decimals / 3))

            if txn_amount >= min_txn_amount:
                time_stamp = datetime.now().astimezone().strftime(time_format)

                message = self.message.format(time_stamp=time_stamp, txn_amount=txn_amount,
                                              token_name=token_name, network=self.network,
                                              txn_hash=txn['hash'], name=self.name)

                # Send formatted Telegram message
                telegram_send_message(message)

                terminal_msg = f"{txn_amount:,} {token_name} swapped on {self.name}"
                log_txns.info(terminal_msg)
                print(f"{time_stamp}\n{terminal_msg}")
