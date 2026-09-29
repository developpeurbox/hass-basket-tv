"""Config flow Basket TV — pré-écran ligue(s), puis sélection des clubs dans ces ligues.

83 clubs au total : une seule liste à cocher serait trop longue. On choisit d'abord
une ou plusieurs ligues (Betclic Élite, Pro B, Euroligue, NBA, Équipes de France),
puis seuls les clubs de ces ligues sont proposés à la sélection.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
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


def _league_options(clubs: dict) -> list[dict]:
    return [{"value": league, "label": league} for league in sorted(clubs.keys())]


def _club_options(clubs: dict, leagues: list[str]) -> tuple[list[dict], dict[str, dict]]:
    """Options de clubs restreintes aux ligues choisies + dict slug -> config club."""
    flat = flatten_clubs(clubs)
    flat = {s: c for s, c in flat.items() if c["league"] in leagues}
    multi_league = len(leagues) > 1
    options = [
        {
            "value": slug,
            "label": f"{cfg['league']} — {cfg.get('name') or slug}" if multi_league
            else (cfg.get("name") or slug),
        }
        for slug, cfg in flat.items()
    ]
    options.sort(key=lambda o: o["label"])
    return options, flat


def _leagues_selector(options: list[dict]):
    return SelectSelector(
        SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
    )


def _clubs_selector(options: list[dict]):
    return SelectSelector(
        SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
    )


class BasketTvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Étape 1 : ligues à suivre. Étape 2 : clubs dans ces ligues."""

    VERSION = 1

    def __init__(self):
        self._clubs: dict = {}
        self._leagues: list[str] = []

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors = {}
        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)

        if user_input is not None:
            self._leagues = user_input.get("leagues", [])
            if not self._leagues:
                errors["leagues"] = "no_league"
            else:
                return await self.async_step_clubs()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("leagues"): _leagues_selector(_league_options(self._clubs))}
            ),
            errors=errors,
        )

    async def async_step_clubs(self, user_input=None):
        errors = {}
        options, flat = _club_options(self._clubs, self._leagues)

        if user_input is not None:
            chosen = user_input.get("clubs", [])
            if not chosen:
                errors["clubs"] = "no_club"
            else:
                selected = {s: flat[s] for s in chosen if s in flat}
                title = ", ".join(sorted(cfg.get("name") or s for s, cfg in selected.items()))
                return self.async_create_entry(title=title, data={"selected": selected})

        return self.async_show_form(
            step_id="clubs",
            data_schema=vol.Schema({vol.Required("clubs"): _clubs_selector(options)}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BasketTvOptionsFlow(config_entry)


class BasketTvOptionsFlow(config_entries.OptionsFlow):
    """Modifier les clubs suivis, par ligue(s) choisie(s).

    Les clubs des ligues non re-sélectionnées à l'étape 1 sont conservés tels quels :
    modifier une ligue ne fait jamais perdre les clubs suivis dans les autres.
    """

    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._clubs: dict = {}
        self._leagues: list[str] = []
        self._current: dict = {}
        self._untouched: dict = {}

    async def async_step_init(self, user_input=None):
        errors = {}
        if not self._clubs:
            self._clubs = await _load_clubs(self.hass)
        if not self._current:
            self._current = dict(self.config_entry.data.get("selected", {}))

        default_leagues = sorted({cfg.get("league", "?") for cfg in self._current.values()})

        if user_input is not None:
            self._leagues = user_input.get("leagues", [])
            if not self._leagues:
                errors["leagues"] = "no_league"
            else:
                # Clubs déjà suivis dans une ligue qu'on ne modifie pas cette fois : conservés.
                self._untouched = {
                    s: c for s, c in self._current.items() if c.get("league") not in self._leagues
                }
                return await self.async_step_clubs()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("leagues", default=default_leagues): _leagues_selector(
                        _league_options(self._clubs)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_clubs(self, user_input=None):
        errors = {}
        options, flat = _club_options(self._clubs, self._leagues)

        # Clubs déjà suivis, mais dont la fiche a disparu du dataset : gardés quand même.
        known = {opt["value"] for opt in options}
        for slug, cfg in self._current.items():
            if cfg.get("league") in self._leagues and slug not in known:
                options.append({"value": slug, "label": f"(retiré du dataset) {slug}"})
                flat[slug] = cfg
        options.sort(key=lambda o: o["label"])

        default_chosen = [
            s for s, c in self._current.items() if c.get("league") in self._leagues
        ]

        if user_input is not None:
            chosen = user_input.get("clubs", [])
            if not chosen:
                errors["clubs"] = "no_club"
            else:
                edited = {s: flat[s] for s in chosen if s in flat}
                selected = {**self._untouched, **edited}
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=", ".join(sorted(cfg.get("name") or s for s, cfg in selected.items())),
                    data={**self.config_entry.data, "selected": selected},
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="clubs",
            data_schema=vol.Schema(
                {vol.Required("clubs", default=default_chosen): _clubs_selector(options)}
            ),
            errors=errors,
        )
