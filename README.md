# Raspipool

**Swimming-pool automation for Home Assistant 2026+**, with an ESP32-based
pool-side controller and a HACS-installable Home Assistant integration.

This is a modernized rewrite of the
[original Raspipool](https://github.com/segalion/raspipool) project
(Raspberry Pi + GPIO + Atlas UART), which was built for Home Assistant ~0.93
in 2019 and relies on APIs that have since been removed.

## What you get

- **ESPHome firmware** for an ESP32 that exposes:
  - Atlas Scientific EZO pH and ORP sensors (I2C)
  - DS18B20 waterproof water-temperature probe
  - 4 relays: main pump, turbo, pH injection pump, ORP injection pump
  - Hard safety interlocks: chemical pumps cannot run without the main pump.
- **`raspipool` Home Assistant integration** (installable via HACS) that adds:
  - Free-chlorine estimate sensor
  - Smoothed pH / ORP sensors
  - Next-filter-cycle duration sensor
  - Bleach / muriatic tank level sensors + tank-level number entities
  - pH / FC / quality / turbo target number entities
  - Bleach / muriatic lock switches
  - Refill / inject quick-action buttons
  - `raspipool.inject_bleach`, `raspipool.inject_muriatic`,
    `raspipool.run_pump_for`, `raspipool.reset_tank` services
  - Config flow with a simple entity-mapping wizard
- **Automation blueprints** for:
  - Daily filter cycle scheduler
  - Automatic chemical balancing
  - Low-tank notifications
  - Pool temperature alerts
- **Modern Lovelace dashboard** replacing the old `ui-lovelace.yaml`.

## Architecture

```
+--------------------+           WiFi / ESPHome Native API
| ESP32 (ESPHome)    |  <---------------------------------->  Home Assistant (HA OS, Pi 4)
|                    |                                         - ESPHome integration (builtin)
|  - Atlas EZO pH    |                                         - raspipool integration (HACS)
|  - Atlas EZO ORP   |                                         - HA dashboard
|  - DS18B20 temp    |
|  - 4x relay GPIO   |
+--------------------+
```

The pool-side Raspberry Pi is no longer required: the Pi now runs Home
Assistant OS, and all direct hardware I/O happens on the ESP32. If you want to
reuse a Pi, you can install Home Assistant OS on it.

## Installation

### 1. Flash the ESP32

See [`esphome/README.md`](esphome/README.md). Install the ESPHome add-on in
Home Assistant, drop `esphome/raspipool-esp32.yaml` into the ESPHome config
directory, create a `secrets.yaml`, and flash the board.

Home Assistant will auto-discover the device and you will be prompted to
confirm its encryption key. All sensors and switches will appear in HA.

### 2. Install the Raspipool integration via HACS

1. Open HACS -> Integrations -> three-dot menu -> Custom repositories.
2. Add `https://github.com/ArrowTech-Labs/raspipool` with category `Integration`.
3. Install **Raspipool**. Restart Home Assistant.
4. Settings -> Devices & Services -> **Add Integration** -> Raspipool.
5. Follow the wizard to map your ESP32 sensors/switches and enter pool
   parameters.

### 3. Install automations and dashboard (optional)

- Import any of the blueprints from [`blueprints/automation/raspipool/`](blueprints/automation/raspipool/)
  via **Settings -> Automations & Scenes -> Blueprints -> Import Blueprint**.
- Create a new dashboard and paste the contents of
  [`lovelace/raspipool.yaml`](lovelace/raspipool.yaml) into its raw-YAML editor.

## Requirements

- Home Assistant 2024.12 or later (tested on 2026.4.2)
- Home Assistant OS on a Raspberry Pi 4 (or any supported platform)
- HACS installed
- ESP32 dev board (e.g. ESP32-WROOM-32)
- Atlas Scientific EZO pH + ORP circuits (I2C mode) and compatible probes
- DS18B20 waterproof temperature probe
- 4-channel 5V relay board
- Peristaltic (or similar) dosing pumps for pH and ORP chemicals

## Migration from the 2019 Raspipool

If you used the original [segalion/raspipool](https://github.com/segalion/raspipool):

1. Remove the old `custom_components/atlas_scientific/` folder and the
   `packages/raspipool/` directory from your HA config. They are preserved
   in [`legacy/`](legacy/) in this repo for reference.
2. Remove `ui-lovelace.yaml` and any `lovelace: mode: yaml` line in
   `configuration.yaml`.
3. Follow the installation steps above.

Every capability of the original YAML-package system is re-created via entity
and blueprint equivalents; a mapping table lives in [`legacy/README.md`](legacy/README.md).

## Publishing new versions (maintainers)

This repository is configured so HACS installs directly from the **default
branch** — you do **not** need to create GitHub Releases. Per the
[HACS publishing rules](https://www.hacs.xyz/docs/publish/start/#versions):

> If the repository does not use tags, the 7 first characters of the last
> commit will be used.
>
> Just publishing tags is not enough, you need to publish releases.

So:

- `git tag v1.2.3 && git push --tags` **does not** register a new version in
  HACS. Git tags without an accompanying GitHub Release are ignored.
- HACS will always install the latest commit of the default branch and show
  the short commit SHA as the remote version in the HACS UI.
- Users still get "update available" notifications whenever a new commit lands.

### Recommended release workflow

1. Bump the `version` field in
   [`custom_components/raspipool/manifest.json`](custom_components/raspipool/manifest.json)
   (this is the version Home Assistant shows on the integration card itself).
2. Commit the change and push to the default branch.
3. Optionally run `git tag v1.2.3 && git push --tags` as a reference marker —
   it has no effect on HACS.

If later on you want HACS to pin to named versions, create a GitHub Release
(`gh release create v1.2.3 --generate-notes`). Until then the tag-or-no-tag
workflow above is all that is required.

## License

MIT - see [LICENSE](LICENSE).
