"""Raspipool service registration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_INJECT_BLEACH,
    SERVICE_INJECT_MURIATIC,
    SERVICE_RESET_TANK,
    SERVICE_RUN_PUMP_FOR,
)
from .coordinator import RaspipoolCoordinator

_LOGGER = logging.getLogger(__name__)

INJECT_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("milliliters"): vol.All(vol.Coerce(float), vol.Range(min=0.0)),
    }
)

RUN_PUMP_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("minutes"): vol.All(vol.Coerce(float), vol.Range(min=0.0)),
    }
)

RESET_TANK_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("tank"): vol.In(["bleach", "muriatic"]),
        vol.Required("liters"): vol.All(vol.Coerce(float), vol.Range(min=0.0)),
    }
)


def _resolve_coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> RaspipoolCoordinator | None:
    """Return the coordinator for `entry_id`, or the only one if unspecified."""
    entries: dict[str, RaspipoolCoordinator] = hass.data.get(DOMAIN, {})
    if not entries:
        return None
    if entry_id:
        return entries.get(entry_id)
    if len(entries) == 1:
        return next(iter(entries.values()))
    return None


def async_register_services(hass: HomeAssistant) -> None:
    """Register the Raspipool services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_INJECT_BLEACH):
        return

    async def _inject_bleach(call: ServiceCall) -> None:
        coord = _resolve_coordinator(hass, call.data.get("entry_id"))
        if coord is None:
            _LOGGER.warning("inject_bleach: no raspipool config entry found")
            return
        await coord.async_inject_bleach(float(call.data["milliliters"]))

    async def _inject_muriatic(call: ServiceCall) -> None:
        coord = _resolve_coordinator(hass, call.data.get("entry_id"))
        if coord is None:
            _LOGGER.warning("inject_muriatic: no raspipool config entry found")
            return
        await coord.async_inject_muriatic(float(call.data["milliliters"]))

    async def _run_pump_for(call: ServiceCall) -> None:
        coord = _resolve_coordinator(hass, call.data.get("entry_id"))
        if coord is None or not coord.source_pump:
            _LOGGER.warning("run_pump_for: no pump configured")
            return
        minutes = float(call.data["minutes"])
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": coord.source_pump}, blocking=True
        )
        hass.loop.call_later(
            minutes * 60,
            lambda: hass.async_create_task(
                hass.services.async_call(
                    "switch",
                    "turn_off",
                    {"entity_id": coord.source_pump},
                    blocking=False,
                )
            ),
        )

    async def _reset_tank(call: ServiceCall) -> None:
        coord = _resolve_coordinator(hass, call.data.get("entry_id"))
        if coord is None:
            return
        tank = call.data["tank"]
        liters = float(call.data["liters"])
        if tank == "bleach":
            coord.async_set_bleach_tank(liters)
        else:
            coord.async_set_muriatic_tank(liters)

    hass.services.async_register(
        DOMAIN, SERVICE_INJECT_BLEACH, _inject_bleach, schema=INJECT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_INJECT_MURIATIC, _inject_muriatic, schema=INJECT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RUN_PUMP_FOR, _run_pump_for, schema=RUN_PUMP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_TANK, _reset_tank, schema=RESET_TANK_SCHEMA
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove Raspipool services."""
    for svc in (
        SERVICE_INJECT_BLEACH,
        SERVICE_INJECT_MURIATIC,
        SERVICE_RUN_PUMP_FOR,
        SERVICE_RESET_TANK,
    ):
        if hass.services.has_service(DOMAIN, svc):
            hass.services.async_remove(DOMAIN, svc)
