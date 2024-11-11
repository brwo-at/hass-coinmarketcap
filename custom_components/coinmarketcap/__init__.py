"""The CoinMarketCap integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN, PLATFORMS, CONF_CRYPTOCURRENCIES

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the CoinMarketCap component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CoinMarketCap from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    _LOGGER.debug("Updating CoinMarketCap configuration")
    
    old_cryptocurrencies = set(entry.data.get(CONF_CRYPTOCURRENCIES, []))
    
    # Reload the config entry
    await hass.config_entries.async_reload(entry.entry_id)
    
    new_cryptocurrencies = set(entry.data.get(CONF_CRYPTOCURRENCIES, []))
    
    removed_cryptocurrencies = old_cryptocurrencies - new_cryptocurrencies
    added_cryptocurrencies = new_cryptocurrencies - old_cryptocurrencies
    
    _LOGGER.debug(f"Old cryptocurrencies: {old_cryptocurrencies}")
    _LOGGER.debug(f"New cryptocurrencies: {new_cryptocurrencies}")
    _LOGGER.debug(f"Removed cryptocurrencies: {removed_cryptocurrencies}")
    _LOGGER.debug(f"Added cryptocurrencies: {added_cryptocurrencies}")
    
    if removed_cryptocurrencies:
        await async_remove_entities(hass, entry, removed_cryptocurrencies)

async def async_remove_entities(hass: HomeAssistant, entry: ConfigEntry, removed_cryptocurrencies):
    """Aggressively remove entities for cryptocurrencies that are no longer tracked."""
    entity_registry = async_get_entity_registry(hass)
    device_registry = async_get_device_registry(hass)

    entities = entity_registry.entities.values()

    for entity_entry in entities:
        if entity_entry.config_entry_id == entry.entry_id:
            for crypto in removed_cryptocurrencies:
                if crypto.lower() in entity_entry.unique_id.lower():
                    _LOGGER.debug(f"Removing entity: {entity_entry.entity_id}")
                    entity_registry.async_remove(entity_entry.entity_id)

                    # If the entity has a device, remove it as well
                    if entity_entry.device_id:
                        device = device_registry.async_get(entity_entry.device_id)
                        if device:
                            _LOGGER.debug(f"Removing device: {device.id}")
                            device_registry.async_remove_device(device.id)

    # Force a reload of the config entry to apply changes
    await hass.config_entries.async_reload(entry.entry_id)