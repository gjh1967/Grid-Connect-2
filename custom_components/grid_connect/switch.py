"""Support for Grid Connect switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DPS_SWITCH, DEFAULT_DPS_SWITCH, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grid Connect switch based on a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]
    
    name = entry.data[CONF_NAME]
    dps_switch = entry.data.get(CONF_DPS_SWITCH, DEFAULT_DPS_SWITCH)
    
    async_add_entities([GridConnectSwitch(device, name, dps_switch)], True)


class GridConnectSwitch(SwitchEntity):
    """Representation of a Grid Connect switch."""

    def __init__(self, device: Any, name: str, dps_switch: str) -> None:
        """Initialize the switch."""
        self._device = device
        self._name = name
        self._dps_switch = dps_switch
        self._is_on = False
        self._available = True

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return if switch is available."""
        return self._available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.hass.async_add_executor_job(
            self._device.set_status, True, int(self._dps_switch)
        )
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.hass.async_add_executor_job(
            self._device.set_status, False, int(self._dps_switch)
        )
        self._is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for the switch."""
        try:
            status = await self.hass.async_add_executor_job(self._device.status)
            
            if status and "dps" in status:
                dps_data = status["dps"]
                if self._dps_switch in dps_data:
                    self._is_on = dps_data[self._dps_switch]
                    self._available = True
                else:
                    _LOGGER.warning(
                        "DPS %s not found in device status: %s",
                        self._dps_switch,
                        dps_data,
                    )
            else:
                _LOGGER.warning("Invalid status response: %s", status)
                self._available = False
                
        except Exception as ex:
            _LOGGER.error("Error updating switch: %s", ex)
            self._available = False
