import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
import logging

from .const import DOMAIN, CONF_API_KEY, CONF_CRYPTOCURRENCIES, CONF_CURRENCY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

TOP_CRYPTOCURRENCIES = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "USDT": "Tether", "BNB": "Binance Coin",
    "ADA": "Cardano", "XRP": "XRP", "DOGE": "Dogecoin", "USDC": "USD Coin",
    "DOT": "Polkadot", "UNI": "Uniswap"
}

class CoinMarketCapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.api_key = None
        self.cryptocurrencies = set()

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Entered async_step_user")
        errors = {}
        if user_input is not None:
            self.api_key = user_input[CONF_API_KEY]
            return await self.async_step_select_cryptocurrencies()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_select_cryptocurrencies(self, user_input=None):
        _LOGGER.debug("Entered async_step_select_cryptocurrencies")
        errors = {}
        if user_input is not None:
            _LOGGER.debug(f"Received user input: {user_input}")
            if user_input.get("add_custom", False):
                _LOGGER.debug("User chose to add custom cryptocurrency")
                # Store the current selection before moving to add_cryptocurrency step
                self.cryptocurrencies.update(user_input.get(CONF_CRYPTOCURRENCIES, []))
                return await self.async_step_add_cryptocurrency()
            else:
                self.cryptocurrencies.update(user_input.get(CONF_CRYPTOCURRENCIES, []))
                if self.cryptocurrencies:
                    _LOGGER.debug(f"Saving configuration with cryptocurrencies: {self.cryptocurrencies}")
                    return self.async_create_entry(
                        title="CoinMarketCap",
                        data={
                            CONF_API_KEY: self.api_key,
                            CONF_CRYPTOCURRENCIES: list(self.cryptocurrencies),
                            CONF_CURRENCY: user_input[CONF_CURRENCY],
                            CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        },
                    )
                else:
                    errors["base"] = "no_cryptocurrencies"

        all_cryptocurrencies = {**TOP_CRYPTOCURRENCIES, **{crypto: crypto for crypto in self.cryptocurrencies if crypto not in TOP_CRYPTOCURRENCIES}}

        _LOGGER.debug(f"Showing form with cryptocurrencies: {all_cryptocurrencies}")
        return self.async_show_form(
            step_id="select_cryptocurrencies",
            data_schema=vol.Schema({
                vol.Optional(CONF_CRYPTOCURRENCIES, default=list(self.cryptocurrencies)): cv.multi_select(all_cryptocurrencies),
                vol.Required(CONF_CURRENCY, default="USD"): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.total_seconds()): int,
                vol.Optional("add_custom"): bool,
            }),
            errors=errors,
        )

    async def async_step_add_cryptocurrency(self, user_input=None):
        _LOGGER.debug("Entered async_step_add_cryptocurrency")
        errors = {}
        if user_input is not None:
            symbol = user_input["symbol"].upper()
            _LOGGER.debug(f"Attempting to add custom cryptocurrency: {symbol}")
            try:
                session = async_get_clientsession(self.hass)
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                params = {"symbol": symbol}
                headers = {"X-CMC_PRO_API_KEY": self.api_key}
                _LOGGER.debug(f"Sending request to CoinMarketCap API: {url}")
                async with session.get(url, params=params, headers=headers) as response:
                    _LOGGER.debug(f"Response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug(f"API response: {data}")
                        if symbol in data["data"]:
                            self.cryptocurrencies.add(symbol)
                            _LOGGER.info(f"Successfully added {symbol} to cryptocurrencies")
                            return await self.async_step_select_cryptocurrencies()
                        else:
                            _LOGGER.warning(f"Symbol {symbol} not found in API response")
                            errors["base"] = "invalid_cryptocurrency"
                    else:
                        _LOGGER.error(f"API request failed with status {response.status}")
                        errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception(f"Unexpected error occurred: {str(e)}")
                errors["base"] = "unknown"

        _LOGGER.debug("Showing form for adding custom cryptocurrency")
        return self.async_show_form(
            step_id="add_cryptocurrency",
            data_schema=vol.Schema({
                vol.Required("symbol"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CoinMarketCapOptionsFlow(config_entry)

class CoinMarketCapOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.cryptocurrencies = set(config_entry.data[CONF_CRYPTOCURRENCIES])

    async def async_step_init(self, user_input=None):
        _LOGGER.debug("Entered CoinMarketCapOptionsFlow.async_step_init")
        errors = {}
        if user_input is not None:
            _LOGGER.debug(f"Received user input: {user_input}")
            if user_input.get("add_custom", False):
                _LOGGER.debug("User chose to add custom cryptocurrency")
                # Store the current selection before moving to add_cryptocurrency step
                self.cryptocurrencies.update(user_input.get(CONF_CRYPTOCURRENCIES, []))
                return await self.async_step_add_cryptocurrency()
            else:
                self.cryptocurrencies = set(user_input.get(CONF_CRYPTOCURRENCIES, []))
                if self.cryptocurrencies:
                    _LOGGER.debug(f"Saving configuration with cryptocurrencies: {self.cryptocurrencies}")
                    new_data = {**self.config_entry.data, CONF_CRYPTOCURRENCIES: list(self.cryptocurrencies)}
                    self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
                    return self.async_create_entry(title="", data={})
                else:
                    errors["base"] = "no_cryptocurrencies"

        all_cryptocurrencies = {**TOP_CRYPTOCURRENCIES, **{crypto: crypto for crypto in self.cryptocurrencies if crypto not in TOP_CRYPTOCURRENCIES}}

        _LOGGER.debug(f"Showing form with cryptocurrencies: {all_cryptocurrencies}")
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_CRYPTOCURRENCIES, default=list(self.cryptocurrencies)): cv.multi_select(all_cryptocurrencies),
                vol.Required(CONF_CURRENCY, default=self.config_entry.data.get(CONF_CURRENCY, "USD")): str,
                vol.Required(CONF_SCAN_INTERVAL, default=self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.total_seconds())): int,
                vol.Optional("add_custom"): bool,
            }),
            errors=errors,
        )

    async def async_step_add_cryptocurrency(self, user_input=None):
        _LOGGER.debug("Entered CoinMarketCapOptionsFlow.async_step_add_cryptocurrency")
        errors = {}
        if user_input is not None:
            symbol = user_input["symbol"].upper()
            _LOGGER.debug(f"Attempting to add custom cryptocurrency: {symbol}")
            try:
                session = async_get_clientsession(self.hass)
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                params = {"symbol": symbol}
                headers = {"X-CMC_PRO_API_KEY": self.config_entry.data[CONF_API_KEY]}
                _LOGGER.debug(f"Sending request to CoinMarketCap API: {url}")
                async with session.get(url, params=params, headers=headers) as response:
                    _LOGGER.debug(f"Response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug(f"API response: {data}")
                        if symbol in data["data"]:
                            self.cryptocurrencies.add(symbol)
                            _LOGGER.info(f"Successfully added {symbol} to cryptocurrencies")
                            return await self.async_step_init()
                        else:
                            _LOGGER.warning(f"Symbol {symbol} not found in API response")
                            errors["base"] = "invalid_cryptocurrency"
                    else:
                        _LOGGER.error(f"API request failed with status {response.status}")
                        errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception(f"Unexpected error occurred: {str(e)}")
                errors["base"] = "unknown"

        _LOGGER.debug("Showing form for adding custom cryptocurrency")
        return self.async_show_form(
            step_id="add_cryptocurrency",
            data_schema=vol.Schema({
                vol.Required("symbol"): str,
            }),
            errors=errors,
        )