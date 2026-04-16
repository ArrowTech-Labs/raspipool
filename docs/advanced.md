# Advanced installation paths

The primary install path for Raspipool is the [Raspipool Installer add-on](../addon-raspipool-installer/README.md).
If you have a non-standard setup or already use HACS, the paths below remain
supported.

## HACS (Home Assistant Community Store)

Raspipool's repository is still HACS-compatible. This is useful if:

- You already manage all of your custom integrations via HACS.
- You are running Home Assistant Core or Container and cannot use add-ons.
- You prefer HACS's update UX over the Raspipool installer add-on.

Steps:

1. Install [HACS](https://www.hacs.xyz/docs/use/download/download/) if you
   haven't already.
2. Open **HACS → Integrations**.
3. Top right **⋮** → **Custom repositories**.
4. URL: `https://github.com/ArrowTech-Labs/raspipool` — **Category:** **Integration** → **Add**.
5. Find **Raspipool** in the list → **Download**, then **restart** Home Assistant.
6. **Settings → Devices & services → Add integration → Raspipool**.

HACS notes:

- The repository's `hacs.json` and `custom_components/raspipool/brand/` assets
  are kept intact specifically so HACS installs keep working.
- HACS installs from the default branch. Version bumps in
  `custom_components/raspipool/manifest.json` show up as updates in HACS.
- You do **not** need to create GitHub Releases; per the
  [HACS publishing docs](https://www.hacs.xyz/docs/publish/start/#versions),
  HACS uses the commit SHA when no release is present.

## Manual copy

If you want neither HACS nor the installer add-on:

1. Copy `custom_components/raspipool/` into your HA `config/custom_components/`.
2. Copy `blueprints/automation/raspipool/` into `config/blueprints/automation/`.
3. Restart Home Assistant and finish setup via **Settings → Devices & services**.

## Why isn't HACS mentioned in the main README?

To keep the first-run experience for new users as simple as possible, the main
README only documents the installer add-on and the manual-copy fallback.
Existing HACS users don't need the README to keep working — their existing
HACS entry continues to pull new commits on its own.
