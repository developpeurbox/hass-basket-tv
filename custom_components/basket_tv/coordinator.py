"""DataUpdateCoordinator Basket TV.

Un flux RSS par club suivi : https://tv-sports.fr/rss/equipe/{code}/{slug}?direct=1
Le titre/description de chaque item contient tout : équipes, compétition, chaîne
(voir parser.py). Pas de scraping HTML, donc peu sensible aux changements de page.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CHANNELS_JSON_URL,
    CLUBS_CACHE_TTL,
    CLUBS_JSON_URL,
    DOMAIN,
    REQUEST_DELAY,
    RSS_URL,
    SCAN_INTERVAL_HOURS,
)
from .data import build_club_data, norm

_LOGGER = logging.getLogger(__name__)

HEADERS = {"User-Agent": "hass-basket-tv (Home Assistant custom integration)"}

# ─── Cache clubs.json ────────────────────────────────────────────────────────
_clubs_cache: dict | None = None
_clubs_cache_ts: float = 0.0


async def load_clubs_async(session: aiohttp.ClientSession, force: bool = False) -> dict:
    """Charge clubs.json : version GitHub (cache 1 h), sinon fichier embarqué."""
    global _clubs_cache, _clubs_cache_ts

    now = time.monotonic()
    if not force and _clubs_cache and (now - _clubs_cache_ts) < CLUBS_CACHE_TTL:
        return _clubs_cache

    try:
        async with session.get(
            CLUBS_JSON_URL, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                _clubs_cache, _clubs_cache_ts = data, now
                return data
            _LOGGER.debug("clubs.json GitHub → HTTP %s, fallback local", resp.status)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("clubs.json GitHub inaccessible : %s — fallback local", err)

    local = Path(__file__).parent / "clubs.json"
    with open(local, encoding="utf-8") as f:
        data = json.load(f)
    if not _clubs_cache:
        _clubs_cache, _clubs_cache_ts = data, now
    return data


# ─── Cache channels.json ─────────────────────────────────────────────────────
_channels_cache: dict | None = None
_channels_cache_ts: float = 0.0


async def load_channels_async(session: aiohttp.ClientSession, force: bool = False) -> dict:
    """Charge channels.json (logo des chaînes) : version GitHub (cache 1 h), sinon fichier embarqué."""
    global _channels_cache, _channels_cache_ts

    now = time.monotonic()
    if not force and _channels_cache and (now - _channels_cache_ts) < CLUBS_CACHE_TTL:
        return _channels_cache

    try:
        async with session.get(
            CHANNELS_JSON_URL, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                _channels_cache, _channels_cache_ts = data, now
                return data
            _LOGGER.debug("channels.json GitHub → HTTP %s, fallback local", resp.status)
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("channels.json GitHub inaccessible : %s — fallback local", err)

    local = Path(__file__).parent / "channels.json"
    with open(local, encoding="utf-8") as f:
        data = json.load(f)
    if not _channels_cache:
        _channels_cache, _channels_cache_ts = data, now
    return data


def flatten_clubs(clubs: dict) -> dict[str, dict]:
    """{"NBA": {"boston-celtics": {...}}} -> {"boston-celtics": {..., "league": "NBA"}}."""
    flat: dict[str, dict] = {}
    for league, teams in clubs.items():
        for slug, cfg in teams.items():
            flat[slug] = {**cfg, "league": league}
    return flat


# ─── Coordinator ─────────────────────────────────────────────────────────────
class BasketTvCoordinator(DataUpdateCoordinator):
    """selected = {"asvel": {"code": 1942, "name": "Asvel", "league": "Betclic Élite", ...}}."""

    def __init__(self, hass: HomeAssistant, selected: dict) -> None:
        self.selected = selected
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(hours=SCAN_INTERVAL_HOURS)
        )

    async def _fetch_rss(self, session: aiohttp.ClientSession, code: int, slug: str) -> str | None:
        url = RSS_URL.format(code=code, slug=slug)
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("baskettv %s → HTTP %s", url, resp.status)
                    return None
                return await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Erreur baskettv %s : %s", url, err)
            return None

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        clubs = flatten_clubs(await load_clubs_async(session))
        logos = {norm(c["name"]): c.get("logo", "") for c in clubs.values() if c.get("name")}
        channels = await load_channels_async(session)
        now = dt_util.now()

        data: dict = {}
        failures = 0
        for i, (slug, cfg) in enumerate(self.selected.items()):
            if i:
                await asyncio.sleep(REQUEST_DELAY)
            code = cfg.get("code") or clubs.get(slug, {}).get("code")
            xml_text = await self._fetch_rss(session, code, slug) if code else None

            if xml_text is None:
                failures += 1
                # On garde la dernière donnée connue plutôt que d'effacer le sensor
                if self.data and slug in self.data:
                    data[slug] = self.data[slug]
                    continue
                data[slug] = build_club_data(slug, cfg, "<rss><channel/></rss>", logos, now, channels)
                continue

            try:
                data[slug] = build_club_data(slug, cfg, xml_text, logos, now, channels)
            except Exception as err:  # noqa: BLE001 — flux mal formé
                _LOGGER.warning("Flux Basket TV illisible pour %s : %s", slug, err)
                failures += 1
                data[slug] = self.data[slug] if self.data and slug in self.data else \
                    build_club_data(slug, cfg, "<rss><channel/></rss>", logos, now, channels)

        if self.selected and failures == len(self.selected):
            raise UpdateFailed("Aucun flux Basket TV n'a pu être récupéré")
        return data
        
