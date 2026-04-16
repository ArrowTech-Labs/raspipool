# Raspipool

**Swimming-pool automation for Home Assistant 2026+**, with an ESP32-based
pool-side controller and a one-click installer add-on for Home Assistant.

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
- **`raspipool` Home Assistant integration** that adds:
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
- **Raspipool Installer add-on** — a tiny Docker add-on with a built-in Ingress
  UI that downloads and installs the integration and blueprints for you.

## Architecture

```
+--------------------+           WiFi / ESPHome Native API
| ESP32 (ESPHome)    |  <---------------------------------->  Home Assistant (HA OS, Pi 4)
|                    |                                         - ESPHome integration (builtin)
|  - Atlas EZO pH    |                                         - raspipool integration
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

### 2. Install the Raspipool integration via the add-on (recommended)

Raspipool ships a small installer add-on that does everything for you — it
copies the integration, installs the blueprints, and exposes a one-click UI
for future updates.

1. Open Home Assistant → **Settings → Add-ons → Add-on Store**.
2. Click the **⋮** menu in the top-right → **Repositories**.
3. Paste:

   ```
   https://github.com/ArrowTech-Labs/raspipool
   ```

4. Click **Add**, then close the dialog. The **Raspipool Installer** add-on
   will appear in the store.
5. Open the add-on → **Install** → **Start**.
6. Click **Open Web UI** (or use the **Raspipool** entry in the left sidebar).
7. In the installer UI:
   - Click **Sync / Update files** (auto-run on first start).
   - Click **Restart Home Assistant**.
8. After HA comes back, go to **Settings → Devices & services → Add integration**,
   search for **Raspipool**, and complete the wizard.

The installer UI keeps a status panel showing the installed integration version,
blueprint count, and Home Assistant version, and provides buttons to re-sync,
download the ESPHome template, and restart HA for future updates.

### 2b. Manual install (fallback)

If you prefer not to use the installer add-on, you can copy the files directly:

1. Copy the [`custom_components/raspipool`](custom_components/raspipool) folder
   into your Home Assistant configuration directory so you have
   `config/custom_components/raspipool/` (same level as `configuration.yaml`).
2. Copy [`blueprints/automation/raspipool`](blueprints/automation/raspipool)
   into `config/blueprints/automation/raspipool/`.
3. Restart Home Assistant.
4. Finish setup via **Settings → Devices & services → Add integration → Raspipool**.

### 3. Install the dashboard (optional)

- Create a new dashboard and paste the contents of
  [`lovelace/raspipool.yaml`](lovelace/raspipool.yaml) into its raw-YAML editor.

## Requirements

- Home Assistant OS (or Supervised) — required for the installer add-on
- Home Assistant 2024.12 or later (tested on 2026.4.2)
- ESP32 dev board (e.g. ESP32-WROOM-32)
- Atlas Scientific EZO pH + ORP circuits (I2C mode) and compatible probes
- DS18B20 waterproof temperature probe
- 4-channel 5V relay board
- Peristaltic (or similar) dosing pumps for pH and ORP chemicals

Manual install works on Home Assistant Core / Container too (no Supervisor
required), but the installer add-on needs HA OS or HA Supervised.

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

The installer add-on downloads the integration payload straight from GitHub at
install/sync time, so there is no separate release artifact to build.

1. Bump the `version` field in
   [`custom_components/raspipool/manifest.json`](custom_components/raspipool/manifest.json)
   (this is the version Home Assistant shows on the integration card itself).
2. Bump `version:` in
   [`addon-raspipool-installer/config.yaml`](addon-raspipool-installer/config.yaml)
   and add an entry to `addon-raspipool-installer/CHANGELOG.md`.
3. Commit both changes to the default branch.
4. Optionally `git tag v1.2.3 && git push --tags` as a reference marker — the
   Supervisor will rebuild the add-on image automatically whenever `version:`
   in the add-on `config.yaml` changes.
5. Existing users see an **update available** badge in the Add-on Store.

## License

MIT - see [LICENSE](LICENSE).
