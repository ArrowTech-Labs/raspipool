"""Raspipool quick-action buttons.

Provides one-tap buttons for common operator actions:
  - Inject next-bleach or next-muriatic dose now
  - Reset cumulative flow stats
  - Refill tanks
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up Raspipool buttons."""
    coordinator: RaspipoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RefillBleachButton(coordinator),
            RefillMuriaticButton(coordinator),
            InjectPlannedBleachButton(coordinator),
            InjectPlannedMuriaticButton(coordinator),
        ]
    )


class RefillBleachButton(RaspipoolEntity, ButtonEntity):
    """Button: mark bleach tank as refilled."""

    _attr_name = "Refill bleach tank"
    _attr_icon = "mdi:bottle-tonic"

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "refill_bleach")

    async def async_press(self) -> None:
        """Reset bleach tank to configured size."""
        from .const import CONF_BLEACH_TANK_SIZE, DEFAULT_BLEACH_TANK_SIZE

        size = self.coordinator._opt(CONF_BLEACH_TANK_SIZE, DEFAULT_BLEACH_TANK_SIZE)
        self.coordinator.async_set_bleach_tank(float(size))


class RefillMuriaticButton(RaspipoolEntity, ButtonEntity):
    """Button: mark muriatic tank as refilled."""

    _attr_name = "Refill muriatic tank"
    _attr_icon = "mdi:bottle-tonic-plus"

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "refill_muriatic")

    async def async_press(self) -> None:
        """Reset muriatic tank to configured size."""
        from .const import CONF_MURIATIC_TANK_SIZE, DEFAULT_MURIATIC_TANK_SIZE

        size = self.coordinator._opt(
            CONF_MURIATIC_TANK_SIZE, DEFAULT_MURIATIC_TANK_SIZE
        )
        self.coordinator.async_set_muriatic_tank(float(size))


class InjectPlannedBleachButton(RaspipoolEntity, ButtonEntity):
    """Button: inject the currently planned bleach dose."""

    _attr_name = "Inject planned bleach dose"
    _attr_icon = "mdi:eyedropper"

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "inject_bleach")

    async def async_press(self) -> None:
        """Run the injection."""
        await self.coordinator.async_inject_bleach(
            self.coordinator.state.next_bleach_ml or 0.0
        )


class InjectPlannedMuriaticButton(RaspipoolEntity, ButtonEntity):
    """Button: inject the currently planned muriatic dose."""

    _attr_name = "Inject planned muriatic dose"
    _attr_icon = "mdi:eyedropper-plus"

    def __init__(self, coordinator: RaspipoolCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "inject_muriatic")

    async def async_press(self) -> None:
        """Run the injection."""
        await self.coordinator.async_inject_muriatic(
            self.coordinator.state.next_muriatic_ml or 0.0
        )
