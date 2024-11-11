import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_CRYPTOCURRENCIES,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL,
    CONF_COIN_AMOUNT,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

async def fetch_top_cryptocurrencies(hass, api_key):
    """Fetch the top 100 cryptocurrencies from CoinMarketCap."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        "X-CMC_PRO_API_KEY": api_key
    }
    params = {
        "start": "1",
        "limit": "100",
        "convert": "USD"
    }

    session = async_get_clientsession(hass)
    
    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return [crypto["symbol"] for crypto in data["data"]]
        else:
            raise Exception(f"Error fetching top cryptocurrencies: {response.status}")

class CoinMarketCapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.api_key = None
        self.cryptocurrencies = set()

    async def async_step_user(self, user_input=None):
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
        errors = {}
        
        if user_input is not None:
            if user_input.get("add_custom", False):
                self.cryptocurrencies.update(user_input.get(CONF_CRYPTOCURRENCIES, []))
                return await self.async_step_add_cryptocurrency()
            else:
                self.cryptocurrencies = set(user_input.get(CONF_CRYPTOCURRENCIES, []))
                if self.cryptocurrencies:
                    return await self.async_step_coin_amounts()
                else:
                    errors["base"] = "no_cryptocurrencies"

        # Fetch top cryptocurrencies
        try:
            top_cryptos = await fetch_top_cryptocurrencies(self.hass, self.api_key)
            all_cryptocurrencies = {crypto: crypto for crypto in top_cryptos}
            all_cryptocurrencies.update({crypto: crypto for crypto in self.cryptocurrencies if crypto not in all_cryptocurrencies})

            return self.async_show_form(
                step_id="select_cryptocurrencies",
                data_schema=vol.Schema({
                    vol.Optional(CONF_CRYPTOCURRENCIES, default=list(self.cryptocurrencies)): cv.multi_select(all_cryptocurrencies),
                    vol.Optional("add_custom"): bool,
                }),
                errors=errors,
            )
        except Exception as e:
            _LOGGER.error(f"Failed to fetch top cryptocurrencies: {e}")
            errors["base"] = "cannot_connect"

    async def async_step_add_cryptocurrency(self, user_input=None):
        errors = {}
        if user_input is not None:
            symbol = user_input["symbol"].upper()
            try:
                session = async_get_clientsession(self.hass)
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                params = {"symbol": symbol}
                headers = {"X-CMC_PRO_API_KEY": self.api_key}
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if symbol in data["data"]:
                            self.cryptocurrencies.add(symbol)
                            return await self.async_step_select_cryptocurrencies()
                        else:
                            errors["base"] = "invalid_cryptocurrency"
                    else:
                        errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception(f"Unexpected error occurred: {str(e)}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="add_cryptocurrency",
            data_schema=vol.Schema({
                vol.Required("symbol"): str,
            }),
            errors=errors,
        )

    async def async_step_coin_amounts(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            try:
                coin_amounts = {}
                for crypto in self.cryptocurrencies:
                    amount_key = f"amount_{crypto}"
                    if amount_key in user_input:
                        coin_amounts[crypto] = str(float(user_input[amount_key]))

                return self.async_create_entry(
                    title="CoinMarketCap",
                    data={
                        CONF_API_KEY: self.api_key,
                        CONF_CRYPTOCURRENCIES: list(self.cryptocurrencies),
                        CONF_CURRENCY: user_input[CONF_CURRENCY],
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                        CONF_COIN_AMOUNT: coin_amounts,
                    },
                )
            except ValueError as e:
                _LOGGER.error(f"Error processing input: {str(e)}")
                errors["base"] = "invalid_input"
            except Exception as e:
                _LOGGER.exception(f"Unexpected error occurred: {str(e)}")
                errors["base"] = "unknown"

        data_schema = {
            vol.Required(CONF_CURRENCY, default="USD"): str,
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.total_seconds()): int,
        }
        
        for crypto in self.cryptocurrencies:
            data_schema[vol.Optional(f"amount_{crypto}", default=0.0)] = str

        return self.async_show_form(
            step_id="coin_amounts",
            data_schema=vol.Schema(data_schema),
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
        errors = {}
        
        if user_input is not None:
            if user_input.get("add_custom", False):
                return await self.async_step_add_cryptocurrency()
            else:
                self.cryptocurrencies = set(user_input.get(CONF_CRYPTOCURRENCIES, []))
                return await self.async_step_coin_amounts()

        # Fetch top cryptocurrencies
        try:
            top_cryptos = await fetch_top_cryptocurrencies(self.config_entry.data[CONF_API_KEY])
            all_cryptocurrencies = {crypto: crypto for crypto in top_cryptos}
            
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({
                    vol.Optional(CONF_CRYPTOCURRENCIES, default=list(self.cryptocurrencies)): cv.multi_select(all_cryptocurrencies),
                    vol.Optional("add_custom"): bool,
                }),
                errors=errors,
            )
        except Exception as e:
            _LOGGER.error(f"Failed to fetch top cryptocurrencies: {e}")
            errors["base"] = "cannot_connect"

    async def async_step_add_cryptocurrency(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            symbol = user_input["symbol"].upper()
            
            try:
                session = async_get_clientsession(self.hass)
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
                params = {"symbol": symbol}
                headers = {"X-CMC_PRO_API_KEY": self.config_entry.data[CONF_API_KEY]}
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if symbol in data["data"]:
                            self.cryptocurrencies.add(symbol)
                            return await self.async_step_init()
                        else:
                            errors["base"] = "invalid_cryptocurrency"
                    else:
                        errors["base"] = "cannot_connect"
                    
            except Exception as e:
                _LOGGER.exception(f"Unexpected error occurred: {str(e)}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="add_cryptocurrency",
            data_schema=vol.Schema({
                vol.Required("symbol"): str,
            }),
            errors=errors,
        )