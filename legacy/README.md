# Legacy Raspipool files

This directory preserves the original 2019 Raspipool configuration for
reference. **Do not copy these files into a modern Home Assistant install.**
They rely on APIs that were removed or deprecated:

- `rpi_gpio` switch platform (removed from Home Assistant core)
- `setup_platform` / `add_devices` integration lifecycle
- `platform: statistics`, `platform: time_date`, `platform: template`
  (legacy format), `platform: history_stats` (legacy format)
- `data_template:`, `icon_template:`, `entity_id:` on template sensors
- `openweathermap` / `pushbullet` YAML configuration
- `lovelace: mode: yaml` + `entity-button` card type

The replacement stack lives one level up:

- `custom_components/raspipool/` - the modern HACS-installable integration
- `esphome/raspipool-esp32.yaml` - ESP32 firmware that replaces direct GPIO
- `blueprints/automation/raspipool/` - automation blueprints that replace the
  YAML automations in `packages/raspipool/`
- `lovelace/raspipool.yaml` - modern dashboard replacing `ui-lovelace.yaml`
