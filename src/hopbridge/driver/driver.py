"""
Configure Chrome settings and initiate it.
"""
from atexit import register

from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager

from src.hopbridge.driver.options import options


# Open Chromium web driver
chrome_driver = Chrome(ChromeDriverManager().install(), options=options)

# Quit chrome driver after whole script has finished execution
register(chrome_driver.quit)
