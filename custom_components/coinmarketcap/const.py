"""Constants for the CoinMarketCap integration."""
from datetime import timedelta

DOMAIN = "coinmarketcap"
CONF_API_KEY = "api_key"
CONF_CRYPTOCURRENCIES = "cryptocurrencies"
CONF_CURRENCY = "currency"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_COIN_AMOUNT = "coin_amount"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

PLATFORMS = ["sensor"]

TOP_CRYPTOCURRENCIES = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "USDT": "Tether", "BNB": "Binance Coin",
    "ADA": "Cardano", "XRP": "XRP", "DOGE": "Dogecoin", "USDC": "USD Coin",
    "DOT": "Polkadot", "UNI": "Uniswap"
}