"""The Grid Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import tinytuya
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_LOCAL_KEY, CONF_PROTOCOL_VERSION, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Grid Connect from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    # Get device configuration
    host = entry.data[CONF_HOST]
    device_id = entry.data[CONF_DEVICE_ID]
    local_key = entry.data[CONF_LOCAL_KEY]
    protocol = entry.data.get(CONF_PROTOCOL_VERSION, "3.3")
    
    # Create device connection
    try:
        device = await hass.async_add_executor_job(
            _create_device, host, device_id, local_key, protocol
        )
    except Exception as ex:
        _LOGGER.error("Failed to connect to device: %s", ex)
        raise ConfigEntryNotReady from ex
    
    # Store device connection
    hass.data[DOMAIN][entry.entry_id] = device
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


def _create_device(host: str, device_id: str, local_key: str, protocol: str) -> Any:
    """Create TinyTuya device connection."""
    device = tinytuya.OutletDevice(dev_id=device_id, address=host, local_key=local_key)
    device.set_version(float(protocol))
    
    # Test connection
    status = device.status()
    if not status or "Error" in str(status):
        raise ConnectionError(f"Failed to connect to device: {status}")
    
    return device


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
