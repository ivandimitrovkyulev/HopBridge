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
    def __init__(self, name: str, bridge_address: str):

        networks = {
            'arbitrum': ['https://api.arbiscan.io', 'https://arbiscan.io'],
            'optimism': ['https://api-optimistic.etherscan.io', 'https://optimistic.etherscan.io'],
            'polygon': ['https://api.polygonscan.com', 'https://polygonscan.com'],
            'gnosis': ['https://blockscout.com/xdai/mainnet/api', 'https://blockscout.com/xdai/mainnet'],
        }
        if name.lower() not in networks:
            raise ValueError(f"No such network. Choose from: {networks}")

        self.name = name.lower()
        self.bridge_address = bridge_address.lower()
        self.network = networks[self.name][1]
        self.network_api = networks[self.name][0]

        self.node_api_key = os.getenv(f"{self.name.upper()}_API_KEY")

        self.abi_endpoint = f"{networks[self.name][0]}/api?module=contract&action=getabi" \
                            "&address={txn_to}" \
                            f"&apikey={self.node_api_key}"

        self.txn_url = f"{networks[self.name][0]}/api?module=account&action=txlist" \
                       "&address={address}&startblock=0&endblock=99999999&sort=desc" \
                       f"&apikey={self.node_api_key}"

        self.erc20_url = f"{networks[self.name][0]}/api?module=account&action=tokentx" \
                         "&contractaddress={token_address}" \
                         "&address={bridge_address}&page=1&offset=100&sort=desc" \
                         f"&apikey={self.node_api_key}"

        self.message = "{time_stamp}\n" \
                       "{txn_amount:,} {token_name} swapped on " \
                       "<a href='{network}/tx/{txn_hash}'>{name}</a>"

        # Create contract instance
        try:
            to_txn = self.get_last_txns(1, self.bridge_address)[-1]['to']
            self.contract_instance = self.create_contract(to_txn)
        except Exception:
            log_error.warning(f"Could not create a contract instance for {self.name}")
            self.contract_instance = None

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

        try:
            hashes = [txn[keyword] for txn in old_list]

            list_diff = [txn for txn in new_list if txn[keyword] not in hashes]

            return list_diff

        except TypeError:
            return []

    def get_last_txns(self, txn_count: int = 1, bridge_address: str = "") -> List:
        """
        Gets the last transactions from a specified contract address.

        :param txn_count: Number of transactions to return
        :param bridge_address: Contract address
        :return: A list of transaction dictionaries
        """
        if txn_count < 1:
            txn_count = 1

        if bridge_address == "":
            bridge_address = self.bridge_address

        txn_url = self.txn_url.format(address=bridge_address)

        try:
            txn_dict = requests.get(txn_url).json()

            # Get a list with number of txns
            last_transactions = txn_dict['result'][:txn_count]

            return last_transactions

        except Exception:
            log_error.warning(f"Error in f'get_last_txns': Unable to fetch transaction data for {self.name}")
            return []

    def get_last_erc20_txns(self, token_address: str, txn_count: int = 1, bridge_address: str = "",
                            filter_by: tuple = ()) -> List:
        """
        Gets the latest Token transactions from a specific smart contract address.

        :param token_address: Address of Token contract of interest
        :param txn_count: Number of transactions to return
        :param bridge_address: Address of the smart contract interacting with Token
        :param filter_by: Filter transactions by field and value, eg. ('to', '0x000...000')
        :return: A list of transaction dictionaries
        """
        if txn_count < 1:
            txn_count = 1

        token_address = token_address.lower()

        if bridge_address == "":
            bridge_address = self.bridge_address

        if self.name == 'gnosis':
            erc20_url = f"{self.network_api}?module=account&action=tokentx&address={self.bridge_address}"
        else:
            erc20_url = self.erc20_url.format(token_address=token_address, bridge_address=bridge_address)

        try:
            txn_dict = requests.get(erc20_url).json()
            # Get a list with number of txns
            last_txns = txn_dict['result'][:txn_count]

        except Exception:
            log_error.warning(f"Error in f'get_last_erc20_txns': Unable to fetch transaction data for {self.name}")
            return []

        try:
            if len(filter_by) != 2:
                temp = {t_dict['hash']: t_dict for t_dict in last_txns}
            else:
                temp = {t_dict['hash']: t_dict for t_dict in last_txns
                        if t_dict[filter_by[0]] == filter_by[1]}

            last_txns_cleaned = [txn for txn in temp.values()]

            return last_txns_cleaned

        except Exception:
            log_error.warning(f"Error in f'get_last_erc20_txns': Unable to filter info for {self.name}")
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
        if self.contract_instance:
            for txn in txns:
                # Simulate contract execution and calculate amount
                contract_output = EvmContract.run_contract(self.contract_instance, txn['input'])
                txn_amount = float(contract_output['amount']) / (10 ** token_decimals)

                rounding = int(token_decimals) // 6
                txn_amount = round(txn_amount, rounding)

                # Construct messages
                time_stamp = datetime.now().astimezone().strftime(time_format)
                message = self.message.format(time_stamp=time_stamp, txn_amount=txn_amount,
                                              token_name=token_name, network=self.network,
                                              txn_hash=txn['hash'], name=self.name)
                terminal_msg = f"{txn['hash']}, {txn_amount:,} {token_name} swapped on {self.name}"

                # Log all transactions
                log_txns.info(terminal_msg)

                if txn_amount >= min_txn_amount:
                    # Send formatted Telegram message
                    telegram_send_message(message)

                    print(f"{time_stamp}\n{terminal_msg}")

    def alert_erc20_txns(self, txns: list, min_txn_amount: float) -> None:
        """
        Checks transaction list and alerts if new transaction is important.

        :param txns: List of transactions
        :param min_txn_amount: Minimum transfer amount to alert for
        :return: None
        """
        for txn in txns:

            txn_amount = float(int(txn['value']) / 10 ** int(txn['tokenDecimal']))
            # round txn amount number
            rounding = int(txn['tokenDecimal']) // 6
            txn_amount = round(txn_amount, rounding)
            token_name = txn['tokenSymbol']

            # Construct messages
            time_stamp = datetime.now().astimezone().strftime(time_format)
            message = self.message.format(time_stamp=time_stamp, txn_amount=txn_amount,
                                          token_name=token_name, network=self.network,
                                          txn_hash=txn['hash'], name=self.name)
            terminal_msg = f"{txn['hash']}, {txn_amount:,} {token_name} swapped on {self.name}"

            # Log all transactions
            log_txns.info(terminal_msg)

            if txn_amount >= min_txn_amount:
                # Send formatted Telegram message
                telegram_send_message(message)

                print(f"{time_stamp} - {terminal_msg}")
