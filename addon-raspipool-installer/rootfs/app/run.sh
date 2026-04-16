#!/usr/bin/with-contenv bashio
# ==============================================================================
# Raspipool Installer - entrypoint
# ==============================================================================
set -e

bashio::log.info "Starting Raspipool Installer add-on..."

LOG_LEVEL="$(bashio::config 'log_level')"
AUTO_SYNC="$(bashio::config 'auto_sync_on_start')"
OVERWRITE_BP="$(bashio::config 'overwrite_blueprints')"

export RASPIPOOL_LOG_LEVEL="${LOG_LEVEL:-info}"
export RASPIPOOL_OVERWRITE_BLUEPRINTS="${OVERWRITE_BP:-false}"
export RASPIPOOL_CONFIG_DIR="/config"
export RASPIPOOL_REPO="ArrowTech-Labs/raspipool"
export RASPIPOOL_REF="${RASPIPOOL_REF:-main}"
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN:-}"

if [[ "${AUTO_SYNC}" == "true" ]]; then
    bashio::log.info "auto_sync_on_start is enabled; running initial sync..."
    if /app/install.sh; then
        bashio::log.info "Initial sync completed."
    else
        bashio::log.warning "Initial sync failed; the Ingress UI can retry manually."
    fi
else
    bashio::log.info "auto_sync_on_start disabled; waiting for user action via Ingress UI."
fi

bashio::log.info "Launching Ingress UI on port 8099..."
exec python3 /app/server.py
