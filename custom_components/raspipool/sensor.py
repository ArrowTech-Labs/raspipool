"""Raspipool sensor entities.

Exposes the derived pool sensors that used to be template sensors in the
legacy YAML packages:

  - Free-chlorine estimate (was ``sensor.e_fc``)
  - Next-cycle duration (was ``sensor.cycle_pool``)
  - Smoothed pH / ORP means (was ``statistics`` platform sensors)
  - Bleach / muriatic tank levels (was ``template`` + ``input_number`` combo)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RaspipoolCoordinator
from .entity import RaspipoolEntity


@dataclass(frozen=True, kw_only=True)
class RaspipoolSensorDescription(SensorEntityDescription):
    """Describes a Raspipool sensor."""

    value_fn: Callable[[RaspipoolCoordinator], float | None]


SENSORS: tuple[RaspipoolSensorDescription, ...] = (
    RaspipoolSensorDescription(
        key="fc_estimate",
        translation_key="fc_estimate",
        name="Free chlorine (estimate)",
        icon="mdi:water-percent",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("fc_estimate") if c.data else None,
    ),
    RaspipoolSensorDescription(
        key="next_cycle_minutes",
        translation_key="next_cycle_minutes",
        name="Next filter cycle",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("next_cycle_minutes") if c.data else None,
    ),
    RaspipoolSensorDescription(
        key="ph_mean",
        translation_key="ph_mean",
        name="pH (smoothed)",
        icon="mdi:alpha-h-circle",
        native_unit_of_measurement="pH",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.state.ph_mean,
    ),
    RaspipoolSensorDescription(
        key="orp_mean",
        translation_key="orp_mean",
        name="ORP (smoothed)",
        icon="mdi:alpha-r-circle",
        native_unit_of_measurement="mV",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.state.orp_mean,
    ),
    RaspipoolSensorDescription(
        key="bleach_tank",
        translation_key="bleach_tank",
        name="Bleach tank",
        icon="mdi:bottle-tonic",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.state.bleach_tank_liters,
    ),
    RaspipoolSensorDescription(
        key="muriatic_tank",
        translation_key="muriatic_tank",
        name="Muriatic tank",
        icon="mdi:bottle-tonic-plus",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.state.muriatic_tank_liters,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Raspipool sensors from a config entry."""
    coordinator: RaspipoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(RaspipoolSensor(coordinator, d) for d in SENSORS)


class RaspipoolSensor(RaspipoolEntity, SensorEntity):
    """Generic Raspipool derived sensor."""

    entity_description: RaspipoolSensorDescription

    def __init__(
        self,
        coordinator: RaspipoolCoordinator,
        description: RaspipoolSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return the current derived value."""
        return self.entity_description.value_fn(self.coordinator)
