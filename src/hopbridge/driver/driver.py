"""
Configure Chrome settings and initiate it.
"""
from atexit import register

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.hopbridge.driver.options import (
    CHROME_LOCATION,
    options,
)


# Open Chromium web driver
chrome_driver = Chrome(ChromeDriverManager().install(), options=options)

# Quit chrome driver after whole script has finished execution
register(chrome_driver.quit)
