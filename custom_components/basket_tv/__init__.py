"""Intégration Basket TV (Betclic Élite / Pro B / NBA) pour Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import BasketTvCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialisation d'une entrée (= une équipe)."""
    selected: dict = entry.data.get("selected", {})

    coordinator = BasketTvCoordinator(hass, selected)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression d'une entrée."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """v1 (une entrée, plusieurs clubs) -> v2 (une entrée par équipe).

    - la 1re entrée garde le 1er club (ordre alphabétique) ;
    - les autres clubs sont retirés de cette entrée (entités supprimées du
      registre) puis recréés dans de nouvelles entrées, avec le même
      unique_id d'entité, donc les mêmes entity_id (sensor.basket_<club>).
    """
    if entry.version == 1:
        selected: dict = dict(entry.data.get("selected", {}))
        if not selected:
            return False

        slugs = sorted(selected)
        keep, others = slugs[0], slugs[1:]

        ent_reg = er.async_get(hass)
        for slug in others:
            unique_id = f"baskettv_{slug.replace('-', '_')}"
            entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
            if entity_id:
                ent_reg.async_remove(entity_id)

        keep_cfg = selected[keep]
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "selected": {keep: keep_cfg}},
            title=keep_cfg.get("name") or keep,
            unique_id=keep,
            version=2,
        )

        for slug in others:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data={"slug": slug, "cfg": selected[slug]},
                )
            )

        _LOGGER.info("basket_tv : migration v1 -> v2 (%d club(s) séparé(s))", len(others))

    return True
