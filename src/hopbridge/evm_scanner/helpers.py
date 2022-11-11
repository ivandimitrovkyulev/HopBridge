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
        swap_amount = arg[1]
        token = arg[2]
        min_amount = arg[3]

        min_amount = f"{min_amount:,} {token}"

        line = [token, from_network, to_network, swap_amount, min_amount, bridge_address]
        table.append(line)

    columns = ["Token", "From_network", "To_network", "Swap_amount", "Min_amount", "Bridge_address"]

    print(tabulate(table, headers=columns, showindex=True,
                   tablefmt="fancy_grid", numalign="left", stralign="left", colalign="left"))


def calculate_swap(contract: EvmContract, swap_amounts: tuple) -> list:
    """
    Calculates the swap out amount for an initialised Evm Contract.

    :param contract: EvmContract instance
    :param swap_amounts: Amount to swap in
    :return: Swap out amount
    """
    out_amounts = []
    for amount in swap_amounts:
        func_args = [1, 0, amount * 10 ** 6]
        try:
            swap_out = EvmContract.run_contract_function(contract.contract, 'calculateSwap', func_args)
            swap_out = swap_out / 10 ** 6

            out_amounts.append(float(swap_out))

        except Exception as e:
            log_error.warning(f"'calculateSwap' Error on {contract.name} - {e}")

    return out_amounts


def alert_arb(swap_ins: Iterable, swap_outs: Iterable, coin: str, min_arb: int, network: str) -> None:
    """
    Checks if arbitrage >= min_arb_required and alerts via Telegram message.

    :param swap_ins: Amounts to swap in
    :param swap_outs: Amounts received
    :param coin: Name of coin being arbitraged
    :param min_arb: Minimum arbitrage required
    :param network: Name of the blockchain network
    :return: None
    """

    url = f"https://app.hop.exchange/#/send?token={coin.upper()}" \
          f"&sourceNetwork=ethereum&destNetwork={network.lower()}"

    for swap_in, swap_out in zip(swap_ins, swap_outs):
        arbitrage = swap_out - swap_in
        if arbitrage >= min_arb:

            timestamp = datetime.now().astimezone().strftime(time_format)
            color_sign = etherscans[network.lower()][2]
            message = f"{timestamp} - hop_contract\n" \
                      f"Swap {swap_in:,} {coin} for {swap_out:,.3f} {coin}; ETH -> {network.upper()}{color_sign}\n" \
                      f"-->Arbitrage: <a href='{url}'>{arbitrage:,.3f} {coin}</a>\n"

            ter_msg = f"{timestamp}\n" \
                      f"Swap {swap_in:,} {coin} for {swap_out:,.3f} {coin} Ethereum -> {network}\n" \
                      f"-->Arbitrage: {arbitrage:,.3f} {coin}\n"

            telegram_send_message(message)
            log_arbitrage.info(ter_msg)


def check_arb(contract: EvmContract, swap_amounts: tuple, coin: str, min_arb: int):
    """
    Checks HOP contract for swap out amount and notifies if arbitrage is found.

    :param contract: EVM contract instance
    :param swap_amounts: Swap out amounts
    :param coin: Coin name
    :param min_arb: Min arbitrage required
    :return:
    """
    network_name = contract.name

    swap_outs = calculate_swap(contract, swap_amounts)

    alert_arb(swap_amounts, swap_outs, coin, min_arb, network_name)
