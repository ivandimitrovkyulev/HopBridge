from datetime import datetime
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.hopbridge.variables import request_wait_time
from src.hopbridge.variables import time_format
from src.hopbridge.message import telegram_send_message
from src.hopbridge.logger import (
    log_arbitrage,
    log_error,
)


def query_hop(
        driver: Chrome,
        amounts: tuple,
        min_arb: float,
        src_network: str = "ethereum",
        dest_network: str = "gnosis",
        token_name: str = "USDC",
) -> None:
    """
    Queries Hop Bridge and checks for arbitrage opportunity.

    :param driver: Chrome webdriver instance
    :param amounts: Amount of token to sell
    :param min_arb: Minimum arb required
    :param src_network: Blockchain to sell from
    :param dest_network: Blockchain to receive from
    :param token_name: Token code, eg. USDC
    """
    driver.get("https://www.google.com/")
    url = f"https://app.hop.exchange/#/send?token={token_name}&sourceNetwork={src_network}" \
          f"&destNetwork={dest_network}"
    driver.get(url)

    all_arbs = {}

    try:

        for amount in range(amounts[0], amounts[1], amounts[2]):

            in_xpath = "//*[@id='root']/div/div[3]/div/div/div[2]/div[2]/div[2]/div/input"
            in_field = WebDriverWait(driver, request_wait_time).until(ec.presence_of_element_located(
                (By.XPATH, in_xpath)))

            in_field.send_keys(Keys.COMMAND + "a")
            in_field.send_keys(Keys.DELETE)
            in_field.send_keys(amount)

            out_xpath = "//*[@id='root']/div/div[3]/div/div/div[4]/div[2]/div[2]/div/input"

            while True:
                out_field = driver.find_element(By.XPATH, out_xpath)
                received = out_field.get_attribute("value")

                if received != "":
                    break

            received = float(received.replace(",", ""))
            arbitrage = received - amount

            timestamp = datetime.now().astimezone().strftime(time_format)
            message = f"{timestamp}\n" \
                      f"{url}\n" \
                      f"Sell {amount:,} {token_name} {src_network} -> {dest_network}\n" \
                      f"\t-->Arbitrage: {arbitrage:,} {token_name}\n"

            # Record all arbs to select the highest later
            all_arbs[arbitrage] = message

        highest_arb = max(all_arbs)
        if highest_arb > min_arb:
            telegram_send_message(all_arbs[highest_arb])
            log_arbitrage.info(all_arbs[highest_arb])
            print(all_arbs[highest_arb])

    except Exception:
        log_error.info(f"Error while querying {url}")
