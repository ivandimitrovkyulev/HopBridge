import os
import json
import requests

from datetime import datetime

from web3 import Web3
from web3.contract import Contract

from src.hopbridge.common.logger import log_txns
from src.hopbridge.variables import time_format
from src.hopbridge.common.message import telegram_send_message


class EvmContract:

    @staticmethod
    def create_contract(txn_to: str, node_api_key: str = "", project_id: str = ""):
        """
        Creates a contract instance ready to be interacted with.

        :param txn_to: Transaction 'to' address
        :param node_api_key: Your node provider's API_KEY access token
        :param project_id: Your project ID
        :return: web3 Contract instance
        """

        if node_api_key == "":
            node_api_key = os.getenv("NODE_API_KEY")

        if project_id == "":
            project_id = os.getenv("PROJECT_ID")

        infura_url = f"https://mainnet.infura.io/v3/{project_id}"
        w3 = Web3(Web3.HTTPProvider(infura_url))

        # Convert transaction to address to check-sum address
        checksum_address = Web3.toChecksumAddress(txn_to)

        # Contract's ABI
        abi_endpoint = f"https://api-optimistic.etherscan.io/api?module=contract&action=getabi" \
                       f"&address={txn_to}&" \
                       f"apikey={node_api_key}"
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


class Txns:

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

    @staticmethod
    def get_last_txns(contract_addr: str, txn_count: int, node_api_key: str = "") -> list:
        """
        Gets the last transactions from a specified contract address.

        :param contract_addr: Contract address , eg. 0xb3C68a491608952Cb1257FC9909a537a0173b63B
        :param txn_count: Number of transactions to return
        :param node_api_key: Your node provider's API_KEY access token
        :return: A list of transactions
        """

        if node_api_key == "":
            node_api_key = os.getenv("NODE_API_KEY")

        if txn_count < 1:
            txn_count = 1

        url = f"https://api-optimistic.etherscan.io/api?module=account&action=txlist" \
              f"&address={contract_addr}&startblock=0&endblock=99999999&sort=desc" \
              f"&apikey={node_api_key}"

        txn_dict = requests.get(url).json()

        # Get a list with number of txns
        last_transactions = txn_dict['result'][:txn_count]

        return last_transactions

    @staticmethod
    def alert_checked_txns(txns: list, min_txn_amount: float, contract_instance: Contract,
                           token_decimals: int, token_name: str, network_name) -> None:
        """
        Checks transaction list and alerts if new transaction is important.

        :param txns: List of transactions
        :param min_txn_amount: Minimum transfer amount to alert for
        :param contract_instance: A web3 Contract instance to be queried
        :param token_decimals: Number of decimals for this coin being swapped
        :param token_name: Token name being swapped
        :param network_name: Name of the blockchain
        :return: None
        """
        for txn in txns:
            # Simulate contract execution and calculate amount
            contract_output = EvmContract.run_contract(contract_instance, txn['input'])
            txn_amount = float(contract_output['amount']) / (10 ** token_decimals)

            if txn_amount >= min_txn_amount:
                time_stamp = datetime.now().astimezone().strftime(time_format)
                message = f"{time_stamp}\n" \
                          f"https://optimistic.etherscan.io/tx/{txn['hash']}\n" \
                          f"{txn_amount:,} {token_name} swapped on {network_name}"

                telegram_send_message(message)
                log_txns.info(message)
                print(message)
