"""Raspipool lock switches.

Replaces the legacy ``input_boolean.lock_bleach`` / ``lock_muriatic``
helpers with real switch entities. When a lock is on, the corresponding
injection service refuses to run.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RaspipoolCoordinator
from .entity import RaspipoolEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Raspipool lock switches."""
    coordinator: RaspipoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RaspipoolLockSwitch(coordinator, "lock_bleach", "Lock bleach"),
            RaspipoolLockSwitch(coordinator, "lock_muriatic", "Lock muriatic"),
            RaspipoolTurboEnableSwitch(coordinator),
        ]
    )


class RaspipoolLockSwitch(RaspipoolEntity, SwitchEntity):
    """A software lock that blocks a chemical injection."""

    _attr_icon = "mdi:lock"

    def __init__(
        self, coordinator: RaspipoolCoordinator, key: str, name: str
    ) -> None:
        """Initialize a lock switch."""
        super().__init__(coordinator, key)
        self._key = key
        self._attr_name = name
        self._state = False

    @property
    def is_on(self) -> bool:
        """Return whether the lock is engaged."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Engage the lock."""
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Release the lock."""
        self._state = False
        self.async_write_ha_state()


class RaspipoolTurboEnableSwitch(RaspipoolEntity, SwitchEntity):
    """Enable/disable turbo-speed cycling."""

    _attr_icon = "mdi:fan"
    _attr_name = "Turbo cycle enabled"

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize the turbo enable switch."""
        super().__init__(coordinator, "turbo_enabled")
        self._state = False

    @property
    def is_on(self) -> bool:
        """Return whether turbo cycle is enabled."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable turbo cycling."""
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable turbo cycling."""
        self._state = False
        self.async_write_ha_state()
