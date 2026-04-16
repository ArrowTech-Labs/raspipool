# Raspipool ESP32 Firmware

This directory contains the [ESPHome](https://esphome.io) firmware configuration
for the pool-side controller. It replaces the old Raspberry Pi GPIO + UART
hardware path used in the 2019 version of Raspipool.

## What it provides

Exposes the following entities to Home Assistant via the ESPHome Native API:

- `sensor.pool_water_temperature` - DS18B20 waterproof probe
- `sensor.pool_ph` - Atlas Scientific EZO pH circuit
- `sensor.pool_orp` - Atlas Scientific EZO ORP circuit
- `switch.pool_pump` - main filtration pump relay
- `switch.pool_turbo` - dual-speed turbo relay (optional)
- `switch.pool_ph_injection` - muriatic acid dosing pump relay
- `switch.pool_orp_injection` - bleach / liquid chlorine dosing pump relay
- calibration buttons for the EZO circuits
- WiFi signal / uptime / status diagnostics

## Hardware

- ESP32 dev board (e.g. ESP32-WROOM-32)
- Atlas Scientific EZO pH circuit + pH probe (I2C mode, default address `0x63`)
- Atlas Scientific EZO ORP circuit + ORP probe (I2C mode, default address `0x62`)
- DS18B20 waterproof 1-wire temperature probe (with 4.7 kOhm pull-up to 3.3V)
- 4-channel relay board (5V, active-low)

### Default pin assignments

| Function        | ESP32 GPIO |
| --------------- | ---------- |
| I2C SDA         | GPIO21     |
| I2C SCL         | GPIO22     |
| DS18B20 (1-Wire)| GPIO4      |
| Pump relay      | GPIO25     |
| Turbo relay     | GPIO26     |
| pH inject relay | GPIO27     |
| ORP inject relay| GPIO14     |

## Installation

1. Install the [ESPHome add-on](https://esphome.io/guides/getting_started_hassio.html)
   in Home Assistant OS (Settings -> Add-ons -> ESPHome Device Builder).
2. Copy `raspipool-esp32.yaml` into your ESPHome config directory.
3. Create a `secrets.yaml` next to it containing:

   ```yaml
   wifi_ssid: "your-ssid"
   wifi_password: "your-password"
   api_encryption_key: "<base64-32-byte-key>"
   ota_password: "<password>"
   ```

   Generate an `api_encryption_key` with:

   ```bash
   python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
   ```

4. In the ESPHome dashboard, install the firmware to the ESP32 (first-time flash
   over USB, subsequent updates OTA).
5. Home Assistant will auto-discover the device. Confirm the encryption key when
   prompted.

## Safety features

The firmware enforces two hard safety interlocks that cannot be bypassed from
Home Assistant:

- Chemical injection pumps refuse to turn on when the main pump is off.
- An interval check forces both injection pumps off every 5 seconds if the main
  pump is not running.

This mirrors the YAML-based `pump_stop` automation from the legacy Raspipool
project, but enforces it on the ESP32 itself so a HA outage cannot leave
chemicals injecting into still water.
