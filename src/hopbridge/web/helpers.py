from tabulate import tabulate
from typing import List


def print_start_message(arguments: List[tuple]) -> None:
    """Prints script start message of all network configurations.

    :param arguments: List of argument lists. Output of func parser_args
    """
    # driver, coin info, in_network, out_network, coin_name, special_chat

    table = []
    for arg in arguments:

        min_arb = arg[1]['min_arb']
        swap_amounts = arg[1]['range']
        from_network = arg[2]
        to_network = arg[3]
        token = arg[4]

        swap_amounts = ", ".join([f"{amount:,}" for amount in range(*swap_amounts)])
        min_arb = f"{min_arb:,} {token}"

        line = [token, from_network, to_network, swap_amounts, min_arb]
        table.append(line)

    columns = ["Token", "From Network", "To Network", "Swap Amounts", "Min Arb."]

    row_ids = [i for i in range(1, len(arguments) + 1)]

    print(tabulate(table, headers=columns, showindex=row_ids,
                   tablefmt="fancy_grid", numalign="left", stralign="left", colalign="left"))
