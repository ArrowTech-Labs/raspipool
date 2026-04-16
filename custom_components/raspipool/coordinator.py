"""Coordinator and in-memory state for Raspipool.

The coordinator is the single source of truth for derived pool state
(bleach/muriatic tank levels, cycle scheduling, injection lockouts). It also
owns the long-running background tasks that replace the legacy YAML
automations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BLEACH_CONCENTRATION,
    CONF_BLEACH_INJECT_SPEED,
    CONF_BLEACH_TANK_SIZE,
    CONF_FC_TARGET,
    CONF_MURIATIC_CONCENTRATION,
    CONF_MURIATIC_INJECT_SPEED,
    CONF_MURIATIC_TANK_SIZE,
    CONF_PH_TARGET,
    CONF_POOL_CAPACITY,
    CONF_POOL_NAME,
    CONF_POOL_QUALITY,
    CONF_POOL_TURNOVER_HOURS,
    CONF_SOURCE_ORP,
    CONF_SOURCE_ORP_INJECT,
    CONF_SOURCE_PH,
    CONF_SOURCE_PH_INJECT,
    CONF_SOURCE_PUMP,
    CONF_SOURCE_TEMPERATURE,
    CONF_SOURCE_TURBO,
    DEFAULT_BLEACH_CONCENTRATION,
    DEFAULT_BLEACH_INJECT_SPEED,
    DEFAULT_BLEACH_TANK_SIZE,
    DEFAULT_FC_TARGET,
    DEFAULT_MURIATIC_CONCENTRATION,
    DEFAULT_MURIATIC_INJECT_SPEED,
    DEFAULT_MURIATIC_TANK_SIZE,
    DEFAULT_PH_TARGET,
    DEFAULT_POOL_CAPACITY,
    DEFAULT_POOL_QUALITY,
    DEFAULT_POOL_TURNOVER_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_ALERT,
    EVENT_CYCLE_START,
    EVENT_INJECTION_START,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class RaspipoolState:
    """Derived runtime state, persisted in the coordinator.

    Values that the user can tweak live (tank levels, targets, cycle offsets)
    are owned here and surfaced as `number` entities so they remain editable
    from the dashboard without requiring YAML.
    """

    bleach_tank_liters: float = 0.0
    muriatic_tank_liters: float = 0.0
    fc_target: float = DEFAULT_FC_TARGET
    ph_target: float = DEFAULT_PH_TARGET
    pool_quality: float = DEFAULT_POOL_QUALITY
    second_cycle_percent: float = 0.0
    turbo_percent: float = 0.0
    out_of_order_days: int = 0
    cycle_minutes: float = 0.0
    next_bleach_ml: float = 0.0
    next_muriatic_ml: float = 0.0
    last_pump_start: datetime | None = None
    last_cycle_start: datetime | None = None
    # Smoothed / statistics
    ph_mean: float | None = None
    orp_mean: float | None = None
    ph_history: list[float] = field(default_factory=list)
    orp_history: list[float] = field(default_factory=list)


class RaspipoolCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for the Raspipool integration.

    Provides:
      - centralized config access for the config entry's source entity map
      - a mutable `state` object shared with every entity
      - background automations that replace the legacy YAML package files
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}:{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.state = RaspipoolState(
            fc_target=self._opt(CONF_FC_TARGET, DEFAULT_FC_TARGET),
            ph_target=self._opt(CONF_PH_TARGET, DEFAULT_PH_TARGET),
            pool_quality=self._opt(CONF_POOL_QUALITY, DEFAULT_POOL_QUALITY),
            bleach_tank_liters=self._opt(
                CONF_BLEACH_TANK_SIZE, DEFAULT_BLEACH_TANK_SIZE
            ),
            muriatic_tank_liters=self._opt(
                CONF_MURIATIC_TANK_SIZE, DEFAULT_MURIATIC_TANK_SIZE
            ),
        )
        self._unsub: list[CALLBACK_TYPE] = []

    # -- Config helpers -----------------------------------------------------

    def _opt(self, key: str, default: Any) -> Any:
        """Read from options with fallback to data, then default."""
        if key in self.entry.options:
            return self.entry.options[key]
        return self.entry.data.get(key, default)

    @property
    def pool_name(self) -> str:
        """User-friendly pool name used for device naming."""
        return self._opt(CONF_POOL_NAME, "Pool")

    @property
    def pool_capacity(self) -> float:
        """Pool capacity in liters."""
        return float(self._opt(CONF_POOL_CAPACITY, DEFAULT_POOL_CAPACITY))

    @property
    def pool_turnover_hours(self) -> float:
        """Design pool turnover time in hours."""
        return float(self._opt(CONF_POOL_TURNOVER_HOURS, DEFAULT_POOL_TURNOVER_HOURS))

    @property
    def bleach_concentration(self) -> float:
        """Bleach / sodium hypochlorite concentration (percent)."""
        return float(
            self._opt(CONF_BLEACH_CONCENTRATION, DEFAULT_BLEACH_CONCENTRATION)
        )

    @property
    def muriatic_concentration(self) -> float:
        """Muriatic acid concentration (percent)."""
        return float(
            self._opt(CONF_MURIATIC_CONCENTRATION, DEFAULT_MURIATIC_CONCENTRATION)
        )

    @property
    def bleach_inject_speed(self) -> float:
        """Bleach dosing pump speed (ml/sec)."""
        return float(
            self._opt(CONF_BLEACH_INJECT_SPEED, DEFAULT_BLEACH_INJECT_SPEED)
        )

    @property
    def muriatic_inject_speed(self) -> float:
        """Muriatic dosing pump speed (ml/sec)."""
        return float(
            self._opt(CONF_MURIATIC_INJECT_SPEED, DEFAULT_MURIATIC_INJECT_SPEED)
        )

    # -- Entity-ID accessors (from config entry) ---------------------------

    def _source(self, key: str) -> str | None:
        return self.entry.data.get(key) or None

    @property
    def source_temperature(self) -> str | None:
        """Entity id for the ESP32 water temperature sensor."""
        return self._source(CONF_SOURCE_TEMPERATURE)

    @property
    def source_ph(self) -> str | None:
        """Entity id for the ESP32 pH sensor."""
        return self._source(CONF_SOURCE_PH)

    @property
    def source_orp(self) -> str | None:
        """Entity id for the ESP32 ORP sensor."""
        return self._source(CONF_SOURCE_ORP)

    @property
    def source_pump(self) -> str | None:
        """Entity id for the ESP32 main pump switch."""
        return self._source(CONF_SOURCE_PUMP)

    @property
    def source_turbo(self) -> str | None:
        """Entity id for the ESP32 turbo pump switch."""
        return self._source(CONF_SOURCE_TURBO)

    @property
    def source_ph_inject(self) -> str | None:
        """Entity id for the ESP32 pH dosing pump switch."""
        return self._source(CONF_SOURCE_PH_INJECT)

    @property
    def source_orp_inject(self) -> str | None:
        """Entity id for the ESP32 ORP dosing pump switch."""
        return self._source(CONF_SOURCE_ORP_INJECT)

    # -- State readers ------------------------------------------------------

    def _get_float(self, entity_id: str | None) -> float | None:
        """Read a numeric state from HA, returning None if unavailable."""
        if not entity_id:
            return None
        st = self.hass.states.get(entity_id)
        if st is None or st.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""):
            return None
        try:
            return float(st.state)
        except (TypeError, ValueError):
            return None

    def _get_bool(self, entity_id: str | None) -> bool | None:
        """Read a boolean state (on/off) from HA, returning None if unavailable."""
        if not entity_id:
            return None
        st = self.hass.states.get(entity_id)
        if st is None or st.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        return st.state == STATE_ON

    # -- DataUpdateCoordinator entry point ---------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Compute derived pool metrics from current HA state."""
        temp = self._get_float(self.source_temperature)
        ph = self._get_float(self.source_ph)
        orp = self._get_float(self.source_orp)
        pump_on = self._get_bool(self.source_pump) or False

        if ph is not None:
            hist = self.state.ph_history
            hist.append(ph)
            if len(hist) > 20:
                del hist[:-20]
            self.state.ph_mean = sum(hist) / len(hist)

        if orp is not None:
            hist = self.state.orp_history
            hist.append(orp)
            if len(hist) > 20:
                del hist[:-20]
            self.state.orp_mean = sum(hist) / len(hist)

        return {
            "temperature": temp,
            "ph": ph,
            "orp": orp,
            "ph_mean": self.state.ph_mean,
            "orp_mean": self.state.orp_mean,
            "pump_on": pump_on,
            "next_cycle_minutes": self.compute_next_cycle_minutes(temp),
            "fc_estimate": self.estimate_fc(ph, orp),
            "bleach_tank": self.state.bleach_tank_liters,
            "muriatic_tank": self.state.muriatic_tank_liters,
        }

    # -- Derived metrics ---------------------------------------------------

    def compute_next_cycle_minutes(self, temperature: float | None) -> float | None:
        """Compute the estimated next-cycle duration in minutes.

        Simplified port of the legacy `sensor.cycle_pool` template:
          base = turnover_minutes * (1 - turbo_fraction * 2/300)
                 * (temp / max(1, 9 - temp/2))
                 / (quality + 6)

        `quality` is a user-provided 1-10 score (higher = better filtration).
        """
        if temperature is None:
            return None
        turnover_min = self.pool_turnover_hours * 60
        turbo_frac = (self.state.turbo_percent or 0.0) / 100.0
        q = max(1.0, self.state.pool_quality + 6)
        t_factor = temperature / max(1.0, 9 - temperature / 2)
        mins = turnover_min * (1 - turbo_frac * 2 / 300) * t_factor / q
        return round(max(0.0, mins), 1)

    def estimate_fc(self, ph: float | None, orp: float | None) -> float | None:
        """Estimate free chlorine from pH and ORP.

        Port of the legacy FC template sensor. Real FC relationship to ORP is
        non-linear and depends on CYA, but a linear approximation is useful
        for trending on a single pool.
        """
        if ph is None or orp is None:
            return None
        # Empirical: FC ~ (ORP - 600) / 100 * (7.5 / ph), clamped at >=0.
        fc = max(0.0, (orp - 600.0) / 100.0 * (7.5 / max(ph, 6.0)))
        return round(fc, 2)

    # -- Mutators (called from number / button entities and services) ------

    @callback
    def async_set_bleach_tank(self, liters: float) -> None:
        """Set the bleach tank level."""
        self.state.bleach_tank_liters = max(0.0, float(liters))
        self.async_update_listeners()

    @callback
    def async_set_muriatic_tank(self, liters: float) -> None:
        """Set the muriatic tank level."""
        self.state.muriatic_tank_liters = max(0.0, float(liters))
        self.async_update_listeners()

    @callback
    def async_set_fc_target(self, value: float) -> None:
        """Update the FC target."""
        self.state.fc_target = float(value)
        self.async_update_listeners()

    @callback
    def async_set_ph_target(self, value: float) -> None:
        """Update the pH target."""
        self.state.ph_target = float(value)
        self.async_update_listeners()

    @callback
    def async_set_pool_quality(self, value: float) -> None:
        """Update pool filtration quality score."""
        self.state.pool_quality = float(value)
        self.async_update_listeners()

    @callback
    def async_set_second_cycle(self, value: float) -> None:
        """Update the second-cycle percentage split."""
        self.state.second_cycle_percent = float(value)
        self.async_update_listeners()

    @callback
    def async_set_turbo(self, value: float) -> None:
        """Update the turbo duty-cycle percentage."""
        self.state.turbo_percent = float(value)
        self.async_update_listeners()

    # -- Automations (replace legacy YAML packages) ------------------------

    @callback
    def async_start_automations(self) -> None:
        """Start background automations for this entry."""
        self._unsub.append(
            async_track_state_change_event(
                self.hass,
                [self.source_pump] if self.source_pump else [],
                self._on_pump_state,
            )
        )
        # Force-refresh EZO readings every 2 minutes while pump is running
        # (mirrors legacy `every_2_min` automation)
        self._unsub.append(
            async_track_time_interval(
                self.hass, self._async_periodic_refresh, timedelta(minutes=2)
            )
        )
        # Hourly tank decrement when injection pumps run
        self._unsub.append(
            async_track_time_interval(
                self.hass, self._async_decrement_tanks, timedelta(minutes=1)
            )
        )
        # Midnight rollover for out-of-order / cycle accounting
        self._unsub.append(
            async_track_time_change(
                self.hass, self._async_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def async_stop_automations(self) -> None:
        """Cancel all automation listeners."""
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()

    @callback
    def _on_pump_state(self, event: Event) -> None:
        """React to pump switch state changes."""
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")
        if new_state is None or old_state is None:
            return
        if old_state.state != STATE_ON and new_state.state == STATE_ON:
            self.state.last_pump_start = dt_util.utcnow()
            self.hass.bus.async_fire(
                EVENT_CYCLE_START,
                {"entry_id": self.entry.entry_id, "pool": self.pool_name},
            )
        elif old_state.state == STATE_ON and new_state.state != STATE_ON:
            # Pump stopped - enforce chemical safety (redundant with ESPHome)
            self.hass.async_create_task(self._async_force_off_injections())

    async def _async_force_off_injections(self) -> None:
        """Turn off both chemical injection pumps."""
        for ent in (self.source_ph_inject, self.source_orp_inject):
            if ent:
                await self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": ent}, blocking=False
                )

    async def _async_periodic_refresh(self, _now: datetime) -> None:
        """Force-refresh EZO readings while pump is running (every 2 min)."""
        if not self._get_bool(self.source_pump):
            return
        entities = [
            e
            for e in (self.source_ph, self.source_orp, self.source_temperature)
            if e
        ]
        if entities:
            await self.hass.services.async_call(
                "homeassistant",
                "update_entity",
                {"entity_id": entities},
                blocking=False,
            )
        await self.async_request_refresh()

    async def _async_decrement_tanks(self, _now: datetime) -> None:
        """Decrement tank levels while injection pumps are running."""
        # 1-minute cadence: subtract inject_speed * 60s / 1000 = liters per min
        if self._get_bool(self.source_ph_inject):
            delta = self.muriatic_inject_speed * 60 / 1000.0
            self.state.muriatic_tank_liters = max(
                0.0, self.state.muriatic_tank_liters - delta
            )
        if self._get_bool(self.source_orp_inject):
            delta = self.bleach_inject_speed * 60 / 1000.0
            self.state.bleach_tank_liters = max(
                0.0, self.state.bleach_tank_liters - delta
            )

        # Low tank alerts
        if self.state.bleach_tank_liters < 1.0:
            self.hass.bus.async_fire(
                EVENT_ALERT,
                {"kind": "bleach_low", "value": self.state.bleach_tank_liters},
            )
        if self.state.muriatic_tank_liters < 1.0:
            self.hass.bus.async_fire(
                EVENT_ALERT,
                {"kind": "muriatic_low", "value": self.state.muriatic_tank_liters},
            )

        self.async_update_listeners()

    async def _async_midnight(self, _now: datetime) -> None:
        """Midnight rollover: decrement out-of-order and refresh."""
        if self.state.out_of_order_days > 0:
            self.state.out_of_order_days -= 1
        await self.async_request_refresh()

    # -- Injection triggers (called by services) ---------------------------

    async def async_inject_bleach(self, milliliters: float) -> None:
        """Run the bleach injection pump long enough to dose `milliliters`."""
        if not self.source_orp_inject:
            return
        seconds = max(0.0, milliliters / max(self.bleach_inject_speed, 0.1))
        self.hass.bus.async_fire(
            EVENT_INJECTION_START, {"kind": "bleach", "ml": milliliters}
        )
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self.source_orp_inject}, blocking=True
        )
        self.hass.loop.call_later(
            seconds,
            lambda: self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch",
                    "turn_off",
                    {"entity_id": self.source_orp_inject},
                    blocking=False,
                )
            ),
        )

    async def async_inject_muriatic(self, milliliters: float) -> None:
        """Run the muriatic injection pump long enough to dose `milliliters`."""
        if not self.source_ph_inject:
            return
        seconds = max(0.0, milliliters / max(self.muriatic_inject_speed, 0.1))
        self.hass.bus.async_fire(
            EVENT_INJECTION_START, {"kind": "muriatic", "ml": milliliters}
        )
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self.source_ph_inject}, blocking=True
        )
        self.hass.loop.call_later(
            seconds,
            lambda: self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch",
                    "turn_off",
                    {"entity_id": self.source_ph_inject},
                    blocking=False,
                )
            ),
        )
