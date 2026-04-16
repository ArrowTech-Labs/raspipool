"""Config flow for the Raspipool integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BLEACH_CONCENTRATION,
    CONF_BLEACH_INJECT_SPEED,
    CONF_BLEACH_TANK_SIZE,
    CONF_FC_TARGET,
    CONF_MURIATIC_CONCENTRATION,
    CONF_MURIATIC_INJECT_SPEED,
    CONF_MURIATIC_TANK_SIZE,
    CONF_NOTIFY_SERVICE,
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
    DEFAULT_POOL_NAME,
    DEFAULT_POOL_QUALITY,
    DEFAULT_POOL_TURNOVER_HOURS,
    DOMAIN,
)


def _sensor_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=Platform.SENSOR)
    )


def _switch_selector() -> selector.EntitySelector:
    return selector.EntitySelectorConfig(domain=Platform.SWITCH)


class RaspipoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Raspipool config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step: pool name and source entity mapping."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            await self.async_set_unique_id(f"raspipool_{user_input[CONF_POOL_NAME]}")
            self._abort_if_unique_id_configured()
            return await self.async_step_pool()

        schema = vol.Schema(
            {
                vol.Required(CONF_POOL_NAME, default=DEFAULT_POOL_NAME): str,
                vol.Required(CONF_SOURCE_TEMPERATURE): _sensor_selector(),
                vol.Required(CONF_SOURCE_PH): _sensor_selector(),
                vol.Required(CONF_SOURCE_ORP): _sensor_selector(),
                vol.Required(CONF_SOURCE_PUMP): selector.EntitySelector(
                    _switch_selector()
                ),
                vol.Optional(CONF_SOURCE_TURBO): selector.EntitySelector(
                    _switch_selector()
                ),
                vol.Required(CONF_SOURCE_PH_INJECT): selector.EntitySelector(
                    _switch_selector()
                ),
                vol.Required(CONF_SOURCE_ORP_INJECT): selector.EntitySelector(
                    _switch_selector()
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_pool(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Second step: pool physical parameters."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_chemistry()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POOL_CAPACITY, default=DEFAULT_POOL_CAPACITY
                ): vol.All(vol.Coerce(int), vol.Range(min=1000, max=1_000_000)),
                vol.Required(
                    CONF_POOL_QUALITY, default=DEFAULT_POOL_QUALITY
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                vol.Required(
                    CONF_POOL_TURNOVER_HOURS, default=DEFAULT_POOL_TURNOVER_HOURS
                ): vol.All(vol.Coerce(float), vol.Range(min=1, max=48)),
            }
        )
        return self.async_show_form(step_id="pool", data_schema=schema)

    async def async_step_chemistry(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Third step: chemistry and dosing parameters."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifications()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PH_TARGET, default=DEFAULT_PH_TARGET
                ): vol.All(vol.Coerce(float), vol.Range(min=6.5, max=8.0)),
                vol.Required(
                    CONF_FC_TARGET, default=DEFAULT_FC_TARGET
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=10.0)),
                vol.Required(
                    CONF_BLEACH_CONCENTRATION, default=DEFAULT_BLEACH_CONCENTRATION
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=15.0)),
                vol.Required(
                    CONF_BLEACH_TANK_SIZE, default=DEFAULT_BLEACH_TANK_SIZE
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=200.0)),
                vol.Required(
                    CONF_BLEACH_INJECT_SPEED, default=DEFAULT_BLEACH_INJECT_SPEED
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=50.0)),
                vol.Required(
                    CONF_MURIATIC_CONCENTRATION,
                    default=DEFAULT_MURIATIC_CONCENTRATION,
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=40.0)),
                vol.Required(
                    CONF_MURIATIC_TANK_SIZE, default=DEFAULT_MURIATIC_TANK_SIZE
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=200.0)),
                vol.Required(
                    CONF_MURIATIC_INJECT_SPEED, default=DEFAULT_MURIATIC_INJECT_SPEED
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=50.0)),
            }
        )
        return self.async_show_form(step_id="chemistry", data_schema=schema)

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Final step: optional notification service."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_POOL_NAME],
                data=self._data,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NOTIFY_SERVICE, default=""): str,
            }
        )
        return self.async_show_form(step_id="notifications", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return RaspipoolOptionsFlow(entry)


class RaspipoolOptionsFlow(OptionsFlow):
    """Options flow: allows editing targets and dosing settings post-install."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Top-level options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        cur = {**self._entry.data, **self._entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PH_TARGET, default=cur.get(CONF_PH_TARGET, DEFAULT_PH_TARGET)
                ): vol.All(vol.Coerce(float), vol.Range(min=6.5, max=8.0)),
                vol.Required(
                    CONF_FC_TARGET, default=cur.get(CONF_FC_TARGET, DEFAULT_FC_TARGET)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=10.0)),
                vol.Required(
                    CONF_POOL_QUALITY,
                    default=cur.get(CONF_POOL_QUALITY, DEFAULT_POOL_QUALITY),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                vol.Required(
                    CONF_POOL_TURNOVER_HOURS,
                    default=cur.get(
                        CONF_POOL_TURNOVER_HOURS, DEFAULT_POOL_TURNOVER_HOURS
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=1, max=48)),
                vol.Required(
                    CONF_BLEACH_CONCENTRATION,
                    default=cur.get(
                        CONF_BLEACH_CONCENTRATION, DEFAULT_BLEACH_CONCENTRATION
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=15.0)),
                vol.Required(
                    CONF_MURIATIC_CONCENTRATION,
                    default=cur.get(
                        CONF_MURIATIC_CONCENTRATION, DEFAULT_MURIATIC_CONCENTRATION
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=40.0)),
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    default=cur.get(CONF_NOTIFY_SERVICE, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
