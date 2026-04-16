#!/usr/bin/env bash
# ==============================================================================
# Raspipool Installer - payload sync
#
# Downloads the Raspipool repository tarball from GitHub and installs:
#   - custom_components/raspipool/       -> /config/custom_components/raspipool/
#   - blueprints/automation/raspipool/   -> /config/blueprints/automation/raspipool/
#
# Idempotent: re-running updates files in place. ESPHome template is NOT
# auto-copied (users download it on demand from the Ingress UI to avoid
# clobbering existing ESPHome configs).
# ==============================================================================
set -euo pipefail

log() { echo "[install] $*"; }
err() { echo "[install:error] $*" >&2; }

CONFIG_DIR="${RASPIPOOL_CONFIG_DIR:-/config}"
REPO="${RASPIPOOL_REPO:-ArrowTech-Labs/raspipool}"
REF="${RASPIPOOL_REF:-main}"
OVERWRITE_BP="${RASPIPOOL_OVERWRITE_BLUEPRINTS:-false}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

TARBALL_URL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}"
# Fall back to tag if ref looks like a version (v1.2.3 or 1.2.3)
if [[ "${REF}" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+ ]]; then
    TARBALL_URL="https://codeload.github.com/${REPO}/tar.gz/refs/tags/${REF}"
fi

log "Downloading payload from ${TARBALL_URL}"
if ! curl -fsSL "${TARBALL_URL}" -o "${WORKDIR}/src.tar.gz"; then
    err "Failed to download tarball. Check network and ref='${REF}'."
    exit 1
fi

log "Extracting payload..."
mkdir -p "${WORKDIR}/src"
tar -xzf "${WORKDIR}/src.tar.gz" -C "${WORKDIR}/src" --strip-components=1

SRC_INTEGRATION="${WORKDIR}/src/custom_components/raspipool"
SRC_BLUEPRINTS="${WORKDIR}/src/blueprints/automation/raspipool"
SRC_ESPHOME="${WORKDIR}/src/esphome"

if [[ ! -d "${SRC_INTEGRATION}" ]]; then
    err "Tarball missing custom_components/raspipool - aborting."
    exit 1
fi

DEST_INTEGRATION="${CONFIG_DIR}/custom_components/raspipool"
DEST_BLUEPRINTS="${CONFIG_DIR}/blueprints/automation/raspipool"

mkdir -p "${CONFIG_DIR}/custom_components" "${CONFIG_DIR}/blueprints/automation"

log "Syncing integration -> ${DEST_INTEGRATION}"
rsync -a --delete \
    --exclude='__pycache__' \
    "${SRC_INTEGRATION}/" "${DEST_INTEGRATION}/"

if [[ -d "${SRC_BLUEPRINTS}" ]]; then
    if [[ "${OVERWRITE_BP}" == "true" ]]; then
        log "Syncing blueprints (overwrite) -> ${DEST_BLUEPRINTS}"
        rsync -a --delete "${SRC_BLUEPRINTS}/" "${DEST_BLUEPRINTS}/"
    else
        log "Syncing blueprints (non-destructive) -> ${DEST_BLUEPRINTS}"
        mkdir -p "${DEST_BLUEPRINTS}"
        rsync -a --ignore-existing "${SRC_BLUEPRINTS}/" "${DEST_BLUEPRINTS}/"
    fi
fi

# Stash the ESPHome template inside the add-on data dir so server.py can serve it.
STASH_DIR="/data/payload"
mkdir -p "${STASH_DIR}"
if [[ -d "${SRC_ESPHOME}" ]]; then
    rsync -a --delete "${SRC_ESPHOME}/" "${STASH_DIR}/esphome/"
fi

# Record install metadata for the UI.
INSTALLED_VERSION="$(grep -E '^\s*"version"' "${DEST_INTEGRATION}/manifest.json" | head -n1 | sed -E 's/.*"version"\s*:\s*"([^"]+)".*/\1/' || echo 'unknown')"
cat > /data/state.json <<EOF
{
  "ref": "${REF}",
  "installed_version": "${INSTALLED_VERSION}",
  "installed_at": "$(date -u +%FT%TZ)",
  "integration_path": "${DEST_INTEGRATION}",
  "blueprints_path": "${DEST_BLUEPRINTS}"
}
EOF

log "Install complete. Integration version: ${INSTALLED_VERSION}"
log "Restart Home Assistant to load the integration (Settings -> System -> Restart)."
