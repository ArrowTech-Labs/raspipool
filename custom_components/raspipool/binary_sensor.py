"""Raspipool binary sensors.

Replaces the legacy ``template`` binary_sensors for ``bleach`` and ``muriatic``
injection state, plus a new ``pump_running`` safety indicator.
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Raspipool binary sensors."""
    coordinator: RaspipoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RaspipoolBleachInjection(coordinator),
            RaspipoolMuriaticInjection(coordinator),
            RaspipoolPumpRunning(coordinator),
        ]
    )


class _BaseBinary(RaspipoolEntity, BinarySensorEntity):
    """Base binary sensor that reacts to coordinator updates."""


class RaspipoolBleachInjection(_BaseBinary):
    """Binary sensor: bleach dosing pump is running."""

    _attr_name = "Bleach injection"
    _attr_icon = "mdi:eyedropper"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "bleach_injection")

    @property
    def is_on(self) -> bool:
        """Return true while the bleach dosing pump is on."""
        return bool(self.coordinator._get_bool(self.coordinator.source_orp_inject))


class RaspipoolMuriaticInjection(_BaseBinary):
    """Binary sensor: muriatic dosing pump is running."""

    _attr_name = "Muriatic injection"
    _attr_icon = "mdi:eyedropper-plus"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "muriatic_injection")

    @property
    def is_on(self) -> bool:
        """Return true while the muriatic dosing pump is on."""
        return bool(self.coordinator._get_bool(self.coordinator.source_ph_inject))


class RaspipoolPumpRunning(_BaseBinary):
    """Binary sensor: main pump is running."""

    _attr_name = "Pump running"
    _attr_icon = "mdi:water-pump"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "pump_running")

    @property
    def is_on(self) -> bool:
        """Return true when the main pump is running."""
        return bool(self.coordinator._get_bool(self.coordinator.source_pump))
