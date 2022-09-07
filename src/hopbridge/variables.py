"""
Set up program variables.
"""
import os
from dotenv import load_dotenv
from urllib3 import Retry
from requests import Session
from requests.adapters import HTTPAdapter


load_dotenv()
# Get env variables
TOKEN = os.getenv("TOKEN")
CHAT_ID_ALERTS = os.getenv("CHAT_ID_ALERTS")
CHAT_ID_SPECIAL = os.getenv("CHAT_ID_SPECIAL")
CHAT_ID_DEBUG = os.getenv("CHAT_ID_DEBUG")


# Set up and configure requests session
http_session = Session()
retry_strategy = Retry(total=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)

time_format = "%Y-%m-%d %H:%M:%S, %Z"

log_format = "%(asctime)s - %(levelname)s - %(message)s"

# Time to wait for page to respond
request_wait_time = 15

# Max time to wait for page to respond
max_request_wait_time = 15

tokens = ("ETH", "USDC", "DAI")
networks = ("ethereum", "polygon", "gnosis", "optimism", "arbitrum")
