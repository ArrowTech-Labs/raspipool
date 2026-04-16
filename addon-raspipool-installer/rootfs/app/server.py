"""Raspipool Installer - Ingress UI + API server.

Serves a small web UI via Home Assistant Ingress that lets the user:
  * see the install state (installed integration version, HA version, blueprint count)
  * sync / re-install the integration from GitHub
  * download the ESPHome template for their ESP32
  * trigger a Home Assistant Core restart
  * jump straight to Devices & services
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

import aiohttp
from aiohttp import web

LOG = logging.getLogger("raspipool_installer")
LOG.setLevel(os.environ.get("RASPIPOOL_LOG_LEVEL", "info").upper())
logging.basicConfig(level=LOG.level)

CONFIG_DIR = Path(os.environ.get("RASPIPOOL_CONFIG_DIR", "/config"))
INTEGRATION_DIR = CONFIG_DIR / "custom_components" / "raspipool"
BLUEPRINT_DIR = CONFIG_DIR / "blueprints" / "automation" / "raspipool"
STATE_FILE = Path("/data/state.json")
STASH_ESPHOME = Path("/data/payload/esphome")
WWW_DIR = Path(__file__).parent / "www"
SUPERVISOR_URL = "http://supervisor"
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json",
    }


async def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            LOG.warning("state.json is corrupt; ignoring")
    return {}


async def _integration_version() -> str | None:
    manifest = INTEGRATION_DIR / "manifest.json"
    if not manifest.exists():
        return None
    try:
        data = json.loads(manifest.read_text())
        return data.get("version")
    except json.JSONDecodeError:
        return None


def _count_blueprints() -> int:
    if not BLUEPRINT_DIR.exists():
        return 0
    return len(list(BLUEPRINT_DIR.glob("*.yaml")))


async def _ha_version(session: aiohttp.ClientSession) -> str | None:
    if not SUPERVISOR_TOKEN:
        return None
    try:
        async with session.get(
            f"{SUPERVISOR_URL}/core/info", headers=_headers(), timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
            return payload.get("data", {}).get("version")
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        LOG.warning("Could not fetch HA version: %s", exc)
        return None


async def handle_status(request: web.Request) -> web.Response:
    state = await _load_state()
    version = await _integration_version()
    blueprints = _count_blueprints()
    async with aiohttp.ClientSession() as session:
        ha_version = await _ha_version(session)
    return web.json_response(
        {
            "installed_version": version,
            "blueprints_count": blueprints,
            "ha_version": ha_version,
            "integration_installed": version is not None,
            "integration_path": str(INTEGRATION_DIR),
            "blueprints_path": str(BLUEPRINT_DIR),
            "last_install": state,
        }
    )


async def handle_sync(request: web.Request) -> web.Response:
    LOG.info("Running install.sh via /api/sync")
    proc = await asyncio.create_subprocess_exec(
        "/app/install.sh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode(errors="replace")
    status = "ok" if proc.returncode == 0 else "error"
    LOG.info("install.sh exited %s", proc.returncode)
    return web.json_response(
        {"status": status, "returncode": proc.returncode, "log": output},
        status=200 if proc.returncode == 0 else 500,
    )


async def handle_restart(request: web.Request) -> web.Response:
    if not SUPERVISOR_TOKEN:
        return web.json_response(
            {"status": "error", "message": "SUPERVISOR_TOKEN missing"}, status=500
        )
    LOG.info("Requesting Home Assistant Core restart via Supervisor API")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SUPERVISOR_URL}/core/restart",
            headers=_headers(),
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            text = await resp.text()
            return web.json_response(
                {"status": "ok" if resp.status == 200 else "error", "supervisor_response": text},
                status=resp.status,
            )


async def handle_esphome_template(request: web.Request) -> web.StreamResponse:
    template = STASH_ESPHOME / "raspipool-esp32.yaml"
    if not template.exists():
        return web.json_response(
            {"status": "error", "message": "ESPHome template not available. Run Sync first."},
            status=404,
        )
    return web.FileResponse(
        template,
        headers={
            "Content-Type": "application/x-yaml",
            "Content-Disposition": 'attachment; filename="raspipool-esp32.yaml"',
        },
    )


async def handle_index(request: web.Request) -> web.Response:
    index = WWW_DIR / "index.html"
    if not index.exists():
        return web.Response(text="Raspipool installer UI missing", status=500)
    return web.Response(text=index.read_text(), content_type="text/html")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/sync", handle_sync)
    app.router.add_post("/api/restart", handle_restart)
    app.router.add_get("/api/esphome-template", handle_esphome_template)
    if WWW_DIR.exists():
        app.router.add_static("/static/", WWW_DIR, show_index=False)
    return app


def main() -> None:
    app = build_app()
    web.run_app(app, host="0.0.0.0", port=8099, print=None)


if __name__ == "__main__":
    main()
