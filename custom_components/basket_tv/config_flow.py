"""Config flow Basket TV — une équipe par entrée.

83 clubs au total : on choisit d'abord la ligue (Betclic Élite, Pro B, Euroligue,
NBA, Équipes de France), puis UN club de cette ligue. Pour suivre plusieurs
équipes, on ajoute l'intégration plusieurs fois.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN
from .coordinator import flatten_clubs, load_clubs_async


async def _load_clubs(hass: HomeAssistant) -> dict:
    session = async_get_clientsession(hass)
    return await load_clubs_async(session, force=True)


def _dropdown(options: list[dict]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, multiple=False, mode=SelectSelectorMode.DROPDOWN)
    )


class BasketTvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Étape 1 : ligue. Étape 2 : un club de cette ligue."""

    VERSION = 2

    def __init__(self):
        self._clubs: dict = {}
        self._league: str = ""

    def _available_flat(self) -> dict[str, dict]:
        """Clubs pas encore configurés (slug -> config + league)."""
        configured = self._async_current_ids()
        return {
            slug: cfg
            for slug, cfg in flatten_clubs(self._clubs).items()
            if slug not in configured
        }

    async def async_step_user(self, user_input=None):
        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)

        available = self._available_flat()
        leagues = sorted({cfg["league"] for cfg in available.values()})
        if not leagues:
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            self._league = user_input["league"]
            return await self.async_step_club()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("league"): _dropdown(
                        [{"value": lg, "label": lg} for lg in leagues]
                    )
                }
            ),
        )

    async def async_step_club(self, user_input=None):
        available = {
            s: c for s, c in self._available_flat().items() if c["league"] == self._league
        }
        if not available:
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            slug = user_input["club"]
            cfg = available[slug]
            await self.async_set_unique_id(slug)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=cfg.get("name") or slug,
                data={"selected": {slug: cfg}},
            )

        options = sorted(
            ({"value": s, "label": c.get("name") or s} for s, c in available.items()),
            key=lambda o: o["label"],
        )
        return self.async_show_form(
            step_id="club",
            data_schema=vol.Schema({vol.Required("club"): _dropdown(options)}),
            description_placeholders={"league": self._league},
        )

    async def async_step_import(self, import_data):
        """Utilisé par la migration v1 -> v2 (une entrée créée par club)."""
        slug = import_data["slug"]
        cfg = import_data["cfg"]
        await self.async_set_unique_id(slug)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=cfg.get("name") or slug,
            data={"selected": {slug: cfg}},
        )
