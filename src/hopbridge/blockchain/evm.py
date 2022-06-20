import os
import json
import requests

from datetime import datetime

from web3 import Web3
from web3.contract import Contract

from src.hopbridge.common.logger import (
    log_txns,
    log_error,
)
from src.hopbridge.variables import time_format
from src.hopbridge.common.message import telegram_send_message


class Network:
    """
    Network configuration class.
    """
    def __init__(self, name: str):
        self.name = name.lower()

        if 'arbitrum' in self.name:
            self.node_api_key = os.getenv("ARBITRUM_API_KEY")

            self.abi_endpoint = "https://api.arbiscan.io/api?module=contract&action=getabi" \
                                "&address={txn_to}" \
                                f"&apikey={self.node_api_key}"

            self.url = "https://api.arbiscan.io/api?module=account&action=txlist" \
                       "&address={address}&startblock=1&endblock=99999999&sort=desc" \
                       f"&apikey={self.node_api_key}"

            self.message = "{time_stamp}\n" \
                           "https://arbiscan.io/tx/{txn_hash}\n" \
                           "{txn_amount:,} {token_name} swapped on Arbitrum"

        elif 'optimism' in self.name:
            self.node_api_key = os.getenv("OPTIMISM_API_KEY")

            self.abi_endpoint = "https://api-optimistic.etherscan.io/api?module=contract&action=getabi" \
                                "&address={txn_to}" \
                                f"&apikey={self.node_api_key}"

            self.url = "https://api-optimistic.etherscan.io/api?module=account&action=txlist" \
                       "&address={address}&startblock=0&endblock=99999999&sort=desc" \
                       f"&apikey={self.node_api_key}"

            self.message = "{time_stamp}\n" \
                           "https://optimistic.etherscan.io/tx/{txn_hash}\n" \
                           "{txn_amount:,} {token_name} swapped on Optimism"


class EvmContract:
    """
    EVM contract and transaction screener class.
    """
    def __init__(self, network: Network):
        self.network = network

    def create_contract(self, txn_to: str) -> Contract:
        """
        Creates a contract instance ready to be interacted with.

        :param txn_to: Transaction 'to' address
        :return: web3 Contract instance
        """
        # Contract's ABI
        abi_endpoint = self.network.abi_endpoint.format(txn_to=txn_to)

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
    def compare_lists(new_list: list, old_list: list, keyword: str = 'hash') -> list:
        """
        Compares two lists of dictionaries.

        :param new_list: New list
        :param old_list: Old list
        :param keyword: Keyword to compare with
        :return: List of dictionaries that are in new list but not in old list
        """
        list_diff = []

        hashes = []
        for txn in old_list:
            hashes.append(txn[keyword])

        for txn in new_list:
            if txn[keyword] not in hashes:
                list_diff.append(txn)

        return list_diff

    def get_last_txns(self, address: str, txn_count: int) -> list:
        """
        Gets the last transactions from a specified contract address.

        :param address: Contract address
        :param txn_count: Number of transactions to return
        :return: A list of transactions
        """
        if txn_count < 1:
            txn_count = 1

        url = self.network.url.format(address=address)

        try:
            txn_dict = requests.get(url).json()

            # Get a list with number of txns
            last_transactions = txn_dict['result'][:txn_count]

            return last_transactions

        except Exception:
            log_error.warning("Error in function 'get_last_txns': Unable to fetch transaction data.")
            return []

    def alert_checked_txns(self, txns: list, min_txn_amount: float, contract_instance: Contract,
                           token_decimals: int, token_name: str) -> None:
        """
        Checks transaction list and alerts if new transaction is important.

        :param txns: List of transactions
        :param min_txn_amount: Minimum transfer amount to alert for
        :param contract_instance: A web3 Contract instance to be queried
        :param token_decimals: Number of decimals for this coin being swapped
        :param token_name: Name of token
        :return: None
        """

        for txn in txns:
            # Simulate contract execution and calculate amount
            contract_output = EvmContract.run_contract(contract_instance, txn['input'])
            txn_amount = float(contract_output['amount']) / (10 ** token_decimals)

            if txn_amount >= min_txn_amount:
                time_stamp = datetime.now().astimezone().strftime(time_format)

                message = self.network.message.format(time_stamp=time_stamp, txn_amount=txn_amount,
                                                      txn_hash=txn['hash'], token_name=token_name)

                telegram_send_message(message)
                log_txns.info(message)
