from datetime import datetime

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
)

from src.hopbridge.common.message import telegram_send_message
from src.hopbridge.common.logger import (
    log_arbitrage,
    log_error,
)
from src.hopbridge.variables import (
    request_wait_time,
    time_format,
)


class WaitForNonEmptyText(object):
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            element_text = ec.find(self.locator).get_attribute("value").strip()
            return element_text != ""
        except StaleElementReferenceException:
            return False


def query_hop(
        driver: Chrome,
        data: dict,
        src_network: str = "ethereum",
        dest_network: str = "gnosis",
        token_name: str = "USDC",
        no_of_queries: int = 1,
) -> None:
    """
    Queries Hop Bridge and checks for arbitrage opportunity.

    :param driver: Chrome webdriver instance
    :param data: Data info with amounts to sell and min. arbitrage
    :param src_network: Blockchain to sell from
    :param dest_network: Blockchain to receive from
    :param token_name: Token code, eg. USDC
    :param no_of_queries: Number of queries
    """
    url = f"https://app.hop.exchange/#/send?token={token_name}&sourceNetwork={src_network}" \
          f"&destNetwork={dest_network}"

    all_arbs = {}

    try:
        # In order to refresh the page
        if no_of_queries > 1:
            driver.get("https://www.google.com/")

        driver.get(url)

    except WebDriverException:
        log_error.warning(f"Error querying {url}")
        return None

    for amount in range(*data['range']):

        xpath = "//*[@id='root']/div/div[3]/div/div/div[2]/div[2]/div[2]/div/input"
        try:
            in_field = WebDriverWait(driver, request_wait_time).until(ec.presence_of_element_located(
                (By.XPATH, xpath)))

        except TimeoutException:
            log_error.warning(f"Element {xpath} not located.")
            return None

        # Clear the entire field
        in_field.send_keys(Keys.CONTROL + "a")
        in_field.send_keys(Keys.DELETE)
        in_field.send_keys(Keys.COMMAND + "a")
        in_field.send_keys(Keys.DELETE)
        # Fill in swap amount
        in_field.send_keys(amount)

        out_xpath = "//*[@id='root']/div/div[3]/div/div/div[4]/div[2]/div[2]/div/input"
        received = WebDriverWait(driver, request_wait_time).until(WaitForNonEmptyText(
            (By.XPATH, out_xpath))).get_attribute("value")

        received = float(received.replace(",", ""))
        arbitrage = received - amount

        decimals = int(data['decimals'])
        arbitrage = round(arbitrage, int(decimals / 3))

        timestamp = datetime.now().astimezone().strftime(time_format)
        message = f"{timestamp}\n" \
                  f"Sell {amount:,} {token_name} {src_network} -> {dest_network}\n" \
                  f"\t-->Arbitrage: <a href='{url}'>{arbitrage:,} {token_name}</a>\n"

        ter_msg = f"Sell {amount:,} {token_name} {src_network} -> {dest_network}\n" \
                  f"\t-->Arbitrage: {arbitrage:,} {token_name}\n"

        # Record all arbs to select the highest later
        all_arbs[arbitrage] = [message, ter_msg]

    highest_arb = max(all_arbs)
    if data['range'][0] > highest_arb > data['min_arb']:
        message = all_arbs[highest_arb][0]
        ter_msg = all_arbs[highest_arb][1]
        telegram_send_message(message)

        log_arbitrage.info(ter_msg)
        timestamp = datetime.now().astimezone().strftime(time_format)
        print(f"{timestamp} - {ter_msg}")
