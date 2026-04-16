"""Constants for the Raspipool integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "raspipool"
MANUFACTURER: Final = "ArrowTech Labs"

# Config entry keys -----------------------------------------------------------
CONF_POOL_NAME: Final = "pool_name"

# Source entities mapped from the ESP32 / ESPHome device
CONF_SOURCE_TEMPERATURE: Final = "source_temperature"
CONF_SOURCE_PH: Final = "source_ph"
CONF_SOURCE_ORP: Final = "source_orp"
CONF_SOURCE_PUMP: Final = "source_pump"
CONF_SOURCE_TURBO: Final = "source_turbo"
CONF_SOURCE_PH_INJECT: Final = "source_ph_inject"
CONF_SOURCE_ORP_INJECT: Final = "source_orp_inject"

# Pool parameters
CONF_POOL_CAPACITY: Final = "pool_capacity"  # liters
CONF_POOL_QUALITY: Final = "pool_quality"
CONF_POOL_TURNOVER_HOURS: Final = "pool_turnover_hours"

# Chemical parameters
CONF_BLEACH_CONCENTRATION: Final = "bleach_concentration"  # percent
CONF_BLEACH_TANK_SIZE: Final = "bleach_tank_size"  # liters
CONF_BLEACH_INJECT_SPEED: Final = "bleach_inject_speed"  # ml/sec
CONF_MURIATIC_CONCENTRATION: Final = "muriatic_concentration"  # percent
CONF_MURIATIC_TANK_SIZE: Final = "muriatic_tank_size"  # liters
CONF_MURIATIC_INJECT_SPEED: Final = "muriatic_inject_speed"  # ml/sec

# Chemistry targets
CONF_PH_TARGET: Final = "ph_target"
CONF_FC_TARGET: Final = "fc_target"  # free chlorine, ppm

# Notifications
CONF_NOTIFY_SERVICE: Final = "notify_service"

# Defaults --------------------------------------------------------------------
DEFAULT_POOL_NAME: Final = "Pool"
DEFAULT_POOL_CAPACITY: Final = 50_000
DEFAULT_POOL_QUALITY: Final = 4
DEFAULT_POOL_TURNOVER_HOURS: Final = 6
DEFAULT_BLEACH_CONCENTRATION: Final = 5.0
DEFAULT_BLEACH_TANK_SIZE: Final = 15.0
DEFAULT_BLEACH_INJECT_SPEED: Final = 2.0
DEFAULT_MURIATIC_CONCENTRATION: Final = 14.0
DEFAULT_MURIATIC_TANK_SIZE: Final = 10.0
DEFAULT_MURIATIC_INJECT_SPEED: Final = 2.0
DEFAULT_PH_TARGET: Final = 7.4
DEFAULT_FC_TARGET: Final = 2.0

DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)

# Platforms -------------------------------------------------------------------
PLATFORMS_KEY: Final = "platforms"

# Service names ---------------------------------------------------------------
SERVICE_INJECT_BLEACH: Final = "inject_bleach"
SERVICE_INJECT_MURIATIC: Final = "inject_muriatic"
SERVICE_RUN_PUMP_FOR: Final = "run_pump_for"
SERVICE_RESET_TANK: Final = "reset_tank"

# Events
EVENT_CYCLE_START: Final = "raspipool_cycle_start"
EVENT_INJECTION_START: Final = "raspipool_injection_start"
EVENT_ALERT: Final = "raspipool_alert"

# Storage keys
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_state"
