from datetime import datetime
from tabulate import tabulate

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


def calculate_swap(contract: EvmContract, swap_amount: float) -> float:
    """
    Calculates the swap out amount for an initialised Evm Contract.

    :param contract: EvmContract instance
    :param swap_amount: Amount to swap in
    :return: Swap out amount
    """
    func_args = [1, 0, swap_amount * 10 ** 6]
    try:
        swap_out = EvmContract.run_contract_function(contract.contract, 'calculateSwap', func_args)
        swap_out = swap_out / 10 ** 6

        return float(swap_out)

    except Exception as e:
        log_error.warning(f"'calculateSwap' Error on {contract.name} - {e}")


def alert_arb(swap_in: float, swap_out: float, coin: str, min_arb: int, network: str) -> None:
    """
    Checks if arbitrage >= min_arb_required and alerts via Telegram message.

    :param swap_in: Amount to swap in
    :param swap_out: Amount received
    :param coin: Name of cain being arbitraged
    :param min_arb: Minimum arbitrage required
    :param network: Name of the blockchain network
    :return: None
    """

    url = f"https://app.hop.exchange/#/send?token={coin.upper()}" \
          f"&sourceNetwork=ethereum&destNetwork={network.lower()}"

    arbitrage = swap_out - swap_in
    if arbitrage >= min_arb:

        timestamp = datetime.now().astimezone().strftime(time_format)
        color_sign = etherscans[network.lower()][2]
        message = f"{timestamp} - scan_contract\n" \
                  f"Swap {swap_in:,} {coin} for {swap_out:,.3f} {coin}; ETH -> {network.upper()}{color_sign}\n" \
                  f"-->Arbitrage: <a href='{url}'>{arbitrage:,.3f} {coin}</a>\n"

        ter_msg = f"{timestamp}\n" \
                  f"Swap {swap_in:,} {coin} for {swap_out:,.3f} {coin} Ethereum -> {network}\n" \
                  f"-->Arbitrage: {arbitrage:,.3f} {coin}\n"

        print(ter_msg)
        telegram_send_message(message)
        log_arbitrage.info(message)


def check_arb(contract: EvmContract, swap_in: float, coin: str, min_arb: int):
    network_name = contract.name

    swap_out = calculate_swap(contract, swap_in)

    alert_arb(swap_in, swap_out, coin, min_arb, network_name)


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
        swap_amount = f"{swap_amount:,} {token}"

        line = [from_network, to_network, swap_amount, min_amount, bridge_address]
        table.append(line)

    columns = ["From_network", "To_network", "Swap_amount", "Min_amount", "Bridge_address"]

    print(tabulate(table, headers=columns, showindex=True,
                   tablefmt="fancy_grid", numalign="left", stralign="left", colalign="left"))
