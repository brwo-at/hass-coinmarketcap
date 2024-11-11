"""Constants for the CoinMarketCap integration."""
from datetime import timedelta

DOMAIN = "coinmarketcap"
CONF_API_KEY = "api_key"
CONF_CRYPTOCURRENCIES = "cryptocurrencies"
CONF_CURRENCY = "currency"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

PLATFORMS = ["sensor"]