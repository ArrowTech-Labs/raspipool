# Raspipool Installer

One-click installer for the Raspipool custom integration, blueprints, and ESPHome template.

## What it does

When you install and start this add-on, it:

1. Downloads the latest Raspipool payload from GitHub.
2. Copies `custom_components/raspipool/` into your Home Assistant `/config/` directory.
3. Copies the Raspipool blueprints into `/config/blueprints/automation/raspipool/`.
4. Exposes a web UI through Home Assistant Ingress so you can:
   - See the installed integration version, blueprint count, and HA version
   - Re-sync / update files with one click
   - Download the ESPHome template for your ESP32 pool controller
   - Trigger a Home Assistant Core restart

## Configuration

| Option | Default | Description |
| --- | --- | --- |
| `log_level` | `info` | Controls add-on log verbosity. |
| `auto_sync_on_start` | `true` | Automatically run the file sync whenever the add-on starts. |
| `overwrite_blueprints` | `false` | If true, blueprints are fully replaced on sync. If false, existing blueprint files are left alone. |

## Post-install

After the first sync you must **restart Home Assistant** (via the add-on UI or via Settings → System → Restart) for Home Assistant to discover the integration. Then go to **Settings → Devices & services → Add integration**, search for **Raspipool**, and run the wizard.

## Safety notes

- The add-on never touches your existing ESPHome configs. The template is available as a download; you decide where it goes.
- Uninstalling the add-on does **not** delete the integration files from `/config`; your data and settings are preserved.
- Sync is idempotent. Re-running it replaces the integration code with the version downloaded from GitHub.
