"""Base entity for the Raspipool integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import RaspipoolCoordinator


class RaspipoolEntity(CoordinatorEntity[RaspipoolCoordinator]):
    """Base entity linked to the Raspipool coordinator and device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RaspipoolCoordinator, unique_suffix: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.pool_name,
            manufacturer=MANUFACTURER,
            model="Raspipool",
            sw_version="1.0.0",
            configuration_url="https://github.com/ArrowTech-Labs/raspipool",
        )
