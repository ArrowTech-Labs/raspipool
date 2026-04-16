"""Raspipool user-adjustable number entities.

Replaces the legacy ``input_number`` helpers. These values are editable from
the dashboard and persist in the coordinator state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RaspipoolCoordinator
from .entity import RaspipoolEntity


@dataclass(frozen=True, kw_only=True)
class RaspipoolNumberDescription(NumberEntityDescription):
    """Number entity description bound to coordinator state."""

    value_fn: Callable[[RaspipoolCoordinator], float]
    set_fn: Callable[[RaspipoolCoordinator, float], None]


NUMBERS: tuple[RaspipoolNumberDescription, ...] = (
    RaspipoolNumberDescription(
        key="fc_target",
        name="FC target",
        icon="mdi:bullseye-arrow",
        native_min_value=0.0,
        native_max_value=10.0,
        native_step=0.1,
        native_unit_of_measurement="ppm",
        mode=NumberMode.BOX,
        value_fn=lambda c: c.state.fc_target,
        set_fn=lambda c, v: c.async_set_fc_target(v),
    ),
    RaspipoolNumberDescription(
        key="ph_target",
        name="pH target",
        icon="mdi:bullseye-arrow",
        native_min_value=6.5,
        native_max_value=8.0,
        native_step=0.05,
        native_unit_of_measurement="pH",
        mode=NumberMode.BOX,
        value_fn=lambda c: c.state.ph_target,
        set_fn=lambda c, v: c.async_set_ph_target(v),
    ),
    RaspipoolNumberDescription(
        key="pool_quality",
        name="Pool quality",
        icon="mdi:star-outline",
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda c: c.state.pool_quality,
        set_fn=lambda c, v: c.async_set_pool_quality(v),
    ),
    RaspipoolNumberDescription(
        key="second_cycle",
        name="Second cycle %",
        icon="mdi:replay",
        native_min_value=0,
        native_max_value=50,
        native_step=5,
        native_unit_of_measurement="%",
        mode=NumberMode.SLIDER,
        value_fn=lambda c: c.state.second_cycle_percent,
        set_fn=lambda c, v: c.async_set_second_cycle(v),
    ),
    RaspipoolNumberDescription(
        key="turbo_percent",
        name="Turbo cycle %",
        icon="mdi:fan",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="%",
        mode=NumberMode.SLIDER,
        value_fn=lambda c: c.state.turbo_percent,
        set_fn=lambda c, v: c.async_set_turbo(v),
    ),
    RaspipoolNumberDescription(
        key="bleach_tank_set",
        name="Bleach tank level",
        icon="mdi:bottle-tonic",
        native_min_value=0,
        native_max_value=200,
        native_step=0.5,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        mode=NumberMode.BOX,
        value_fn=lambda c: c.state.bleach_tank_liters,
        set_fn=lambda c, v: c.async_set_bleach_tank(v),
    ),
    RaspipoolNumberDescription(
        key="muriatic_tank_set",
        name="Muriatic tank level",
        icon="mdi:bottle-tonic-plus",
        native_min_value=0,
        native_max_value=200,
        native_step=0.5,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        mode=NumberMode.BOX,
        value_fn=lambda c: c.state.muriatic_tank_liters,
        set_fn=lambda c, v: c.async_set_muriatic_tank(v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Raspipool number entities."""
    coordinator: RaspipoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(RaspipoolNumber(coordinator, d) for d in NUMBERS)


class RaspipoolNumber(RaspipoolEntity, NumberEntity):
    """User-adjustable number backed by coordinator state."""

    entity_description: RaspipoolNumberDescription

    def __init__(
        self,
        coordinator: RaspipoolCoordinator,
        description: RaspipoolNumberDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return float(self.entity_description.value_fn(self.coordinator))

    async def async_set_native_value(self, value: float) -> None:
        """Set the new value via the coordinator."""
        self.entity_description.set_fn(self.coordinator, value)
        self.async_write_ha_state()
