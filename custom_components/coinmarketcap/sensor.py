"""Support for CoinMarketCap sensors."""

from datetime import timedelta
import logging
from decimal import Decimal

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_API_KEY, CONF_CRYPTOCURRENCIES, CONF_CURRENCY, CONF_SCAN_INTERVAL, CONF_COIN_AMOUNT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up CoinMarketCap sensor from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    cryptocurrencies = entry.data[CONF_CRYPTOCURRENCIES]
    currency = entry.data[CONF_CURRENCY]
    scan_interval = timedelta(seconds=entry.data[CONF_SCAN_INTERVAL])
    coin_amounts = entry.data.get(CONF_COIN_AMOUNT, {})

    coordinator = CoinMarketCapDataUpdateCoordinator(hass, api_key, cryptocurrencies, currency, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        CoinMarketCapSensor(coordinator, crypto, coin_amounts.get(crypto, 0))
        for crypto in cryptocurrencies
    ]
    
    # Add Total Portfolio Value sensor
    sensors.append(CoinMarketCapTotalValueSensor(coordinator, coin_amounts))

    async_add_entities(sensors)

class CoinMarketCapDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching CoinMarketCap data."""

    def __init__(self, hass, api_key, cryptocurrencies, currency, scan_interval):
        """Initialize."""
        self.api_key = api_key
        self.cryptocurrencies = cryptocurrencies
        self.currency = currency
        self.session = async_get_clientsession(hass)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=scan_interval)

    async def _async_update_data(self):
        """Fetch data from CoinMarketCap."""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {
                "symbol": ",".join(self.cryptocurrencies),
                "convert": self.currency,
            }
            headers = {
                "X-CMC_PRO_API_KEY": self.api_key,
            }

            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error communicating with CoinMarketCap: {response.status}")

                data = await response.json()
                return {
                    symbol: data["data"][symbol]["quote"][self.currency]["price"]
                    for symbol in self.cryptocurrencies
                }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with CoinMarketCap: {err}")

class CoinMarketCapSensor(SensorEntity):
    """Representation of a CoinMarketCap sensor."""

    def __init__(self, coordinator, cryptocurrency, amount):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.cryptocurrency = cryptocurrency
        self.amount = Decimal(str(amount))

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.cryptocurrency} Value"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self.cryptocurrency}_value_{self.coordinator.currency}"

    @property
    def state(self):
        """Return the state of the sensor."""
        price = self.coordinator.data.get(self.cryptocurrency)
        
        if price is not None:
            total_value = Decimal(str(price)) * self.amount
            return round(float(total_value), 2)
        
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self.coordinator.currency

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:currency-usd"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "cryptocurrency": self.cryptocurrency,
            "amount": str(self.amount),
            "price": self.coordinator.data.get(self.cryptocurrency),
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self):
        """Update the entity."""
        await self.coordinator.async_request_refresh()

class CoinMarketCapTotalValueSensor(SensorEntity):
    """Representation of a CoinMarketCap Total Portfolio Value sensor."""

    def __init__(self, coordinator, coin_amounts):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.coin_amounts = {crypto: Decimal(str(amount)) for crypto, amount in coin_amounts.items()}

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Total Portfolio Value"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_total_portfolio_value_{self.coordinator.currency}"

    @property
    def state(self):
        """Return the state of the sensor."""
        total_value = Decimal('0')
        for crypto, amount in self.coin_amounts.items():
            price = self.coordinator.data.get(crypto)
            if price is not None:
                total_value += Decimal(str(price)) * amount
        return round(float(total_value), 2)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self.coordinator.currency

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:currency-usd"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "cryptocurrencies": list(self.coin_amounts.keys()),
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self):
        """Update the entity."""
        await self.coordinator.async_request_refresh()