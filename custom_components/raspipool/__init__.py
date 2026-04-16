"""Raspipool: Swimming-pool automation integration for Home Assistant.

This integration is the modernized successor to the original Raspipool YAML
packages. It exposes derived pool entities (free-chlorine estimate, cycle time,
tank levels, injection status) on top of an ESPHome-based ESP32 controller
that owns the pH, ORP, temperature sensors and the pump / chemical dosing
relays.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import RaspipoolCoordinator
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Raspipool integration from YAML (no-op, UI only)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Raspipool from a config entry."""
    coordinator = RaspipoolCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async_register_services(hass)

    coordinator.async_start_automations()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Raspipool config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: RaspipoolCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.async_stop_automations()

    if not hass.data[DOMAIN]:
        async_unregister_services(hass)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload on options update."""
    await hass.config_entries.async_reload(entry.entry_id)
