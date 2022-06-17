<h1>HopBridge</h1>
<h3>version 0.1.0</h3>

Program that screens https://hop.exchange for arbitrage and etherscan for contract transactions and alerts via a Telegram message.

<br> 

## Installation
<br>

This project uses **Python 3.9** and requires a
[Chromium WebDriver](https://chromedriver.chromium.org/getting-started/) installed.

Clone the project:
```
git clone https://github.com/ivandimitrovkyulev/HopBridge

cd HopBridge
```

Create a virtual environment in the current working directory and activate it:

```
poetry shell
```

Install all third-party project dependencies:
```
poetry install
```

You will also need to save the following variables in a **.env** file in .../HopBridge:
```
CHROME_LOCATION=<your/web/driver/path/location> 

TOKEN=<telegram-token-for-your-bot>

CHAT_ID_ALERTS=<id-of-telegram-chat-for-alerts>

CHAT_ID_DEBUG=<id-of-telegram-chat-for-debugging>

CHAT_ID_SPECIAL=<id-of-telegram-chat-for-special-alerts>

WEB3_INFURA_PROJECT_ID=<project-id-from-node>

PROJECT_ID=<project-id-from-node>

NODE_API_KEY=<etherscan-api-key>
```
<br/>

## Running the script
<br/>

To screen the hop-bridge website:
```
var="$(cat input.json)"
python3 main.py "$var"
```
<br>

To screen etherscan for contract transactions:
```
var="$(cat contracts.json)"
python3 etherscan.py "$var"
```