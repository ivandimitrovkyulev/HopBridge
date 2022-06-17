from time import sleep
from typing import Optional

from requests.exceptions import ConnectionError
from requests import (
    post,
    Response,
)
from src.hopbridge.common.logger import log_error
from src.hopbridge.variables import (
    TOKEN,
    CHAT_ID_ALERTS,
    CHAT_ID_DEBUG,
)


def telegram_send_message(
        message_text: str,
        disable_web_page_preview: bool = True,
        telegram_token: Optional[str] = "",
        telegram_chat_id: Optional[str] = "",
        debug: bool = False,
) -> Response:
    """
    Sends a Telegram message to a specified chat.
    Must have a .env file with the following variables:
    TOKEN: your Telegram access token.
    CHAT_ID: the specific id of the chat you want the message sent to
    Follow telegram's instruction on how to set up a bot using the bot father
    and configure it to be able to send messages to a chat.

    :param message_text: Text to be sent to the chat
    :param disable_web_page_preview: Set web preview on/off
    :param telegram_token: Telegram TOKEN API, default take from .env
    :param telegram_chat_id: Telegram chat ID for alerts, default is 'CHAT_ID_ALERTS' from .env file
    :param debug: If true sends message to Telegram chat with 'CHAT_ID_DEBUG' from .env file
    :return: requests.Response
    """
    telegram_token = str(telegram_token)
    telegram_chat_id = str(telegram_chat_id)

    # if URL not provided - try TOKEN variable from the .env file
    if telegram_token == "":
        telegram_token = TOKEN

    # if chat_id not provided - try CHAT_ID_ALERTS or CHAT_ID_DEBUG variable from the .env file
    if telegram_chat_id == "":
        if debug:
            telegram_chat_id = CHAT_ID_DEBUG
        else:
            telegram_chat_id = CHAT_ID_ALERTS

    # construct url using token for a sendMessage POST request
    url = "https://api.telegram.org/bot{}/sendMessage".format(telegram_token)

    # Construct data for the request
    data = {"chat_id": telegram_chat_id, "text": message_text,
            "disable_web_page_preview": disable_web_page_preview}

    # send the POST request
    while True:
        try:
            post_request = post(url, data)

            return post_request

        except ConnectionError:
            log_error.warning(f"Error while trying to send a Telegram message.")
            sleep(3)
