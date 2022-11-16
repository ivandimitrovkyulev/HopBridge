from datetime import datetime
from tabulate import tabulate
from typing import Iterable

from src.hopbridge.blockchain.evm import EvmContract
from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.common.logger import (
    log_error,
    log_arbitrage,
)
from src.hopbridge.variables import (
    time_format,
    etherscans,
)


def print_start_message(arguments: list) -> None:
    """Prints script start message of all network configurations.

    :param arguments: List of argument lists. Output of func parser_args
    """

    table = []
    for arg in arguments:
        from_network = 'ethereum'
        to_network = arg[0].name
        bridge_address = arg[0].contract_address.lower()
        swap_amount = [f"{amount:,}" for amount in arg[1]]

        token = arg[2]
        min_amount = arg[3]

        min_amount = f"{min_amount} {token}"
        swap_amount = ", ".join(swap_amount)

        line = [token, from_network, to_network, swap_amount, min_amount, bridge_address]
        table.append(line)

    columns = ["Token", "From", "To", "Swap_amounts", "Min_arb", "Bridge_address"]

    print(tabulate(table, headers=columns, showindex=True,
                   tablefmt="fancy_grid", numalign="left", stralign="left", colalign="left"))


def calculate_swap(contract: EvmContract, swap_amounts: tuple, decimals: int) -> list:
    """
    Calculates the swap out amount for an initialised Evm Contract.

    :param contract: EvmContract instance
    :param swap_amounts: Amount to swap in
    :param decimals: Token decimals precision
    :return: Swap out amount
    """

    out_amounts = []
    for amount in swap_amounts:
        func_args = [1, 0, amount * 10 ** decimals]
        try:
            swap_out = EvmContract.run_contract_function(contract.contract, 'calculateSwap', func_args)
            swap_out = swap_out / 10 ** decimals

            out_amounts.append(float(swap_out))

        except Exception as e:
            log_error.warning(f"'calculateSwap' Error on {contract.name} - {e}")

    return out_amounts


def alert_arb(swap_ins: Iterable, swap_outs: Iterable, token: str, min_arb: int, network: str) -> None:
    """
    Checks if arbitrage >= min_arb_required and alerts via Telegram message.

    :param swap_ins: Amounts to swap in
    :param swap_outs: Amounts received
    :param token: Name of token being arbitraged
    :param min_arb: Minimum arbitrage required
    :param network: Name of the blockchain network
    :return: None
    """

    url = f"https://app.hop.exchange/#/send?token={token.upper()}" \
          f"&sourceNetwork=ethereum&destNetwork={network.lower()}"

    for swap_in, swap_out in zip(swap_ins, swap_outs):
        arbitrage = swap_out - swap_in
        if arbitrage >= min_arb:

            timestamp = datetime.now().astimezone().strftime(time_format)
            color_sign = etherscans[network.lower()][2]
            message = f"{timestamp} - hop_contract\n" \
                      f"Swap {swap_in:,} {token} for {swap_out:,.3f} {token}; ETH -> {network.upper()}{color_sign}\n" \
                      f"-->Arbitrage: <a href='{url}'>{arbitrage:,.3f} {token}</a>\n"

            ter_msg = f"{timestamp}\n" \
                      f"Swap {swap_in:,} {token} for {swap_out:,.3f} {token} Ethereum -> {network}\n" \
                      f"-->Arbitrage: {arbitrage:,.3f} {token}\n"

            telegram_send_message(message)
            log_arbitrage.info(ter_msg)


def check_arb(contract: EvmContract, swap_amounts: tuple, decimals: int, token: str, min_arb: int) -> None:
    """
    Checks HOP contract for swap out amount and notifies if arbitrage is found.

    :param contract: EVM contract instance
    :param swap_amounts: Swap out amounts
    :param decimals: Token decimals precision
    :param token: Token name
    :param min_arb: Min arbitrage required
    :return:
    """
    network_name = contract.name

    swap_outs = calculate_swap(contract, swap_amounts, decimals)

    alert_arb(swap_amounts, swap_outs, token, min_arb, network_name)
