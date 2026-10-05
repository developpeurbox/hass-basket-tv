"""Entités sensor Basket TV."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BasketTvCoordinator

EMPTY_ATTRS = {
    "team": "", "logoTeam": "", "competition": "", "journee": "",
    "domicile": "", "logoDomicile": "", "shortDomicile": "",
    "exterieur": "", "logoExterieur": "", "shortExterieur": "",
    "situation": "", "date": "", "date_fr": "",
    "datetime": "", "datetime_fin": "", "display": False,
    "heure": "",
    "diffuseur1": "", "logoDiffuseur1": "",
    "diffuseur2": "", "logoDiffuseur2": "",
    "chaines": [],
    "game": "", "lien_match": "", "scraped_at": "",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BasketTvCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [BasketTvSensor(coordinator, slug, cfg) for slug, cfg in coordinator.selected.items()],
        update_before_add=True,
    )


class BasketTvSensor(CoordinatorEntity, SensorEntity):
    """Un sensor = un club suivi ; état = chaîne du prochain match télévisé."""

    def __init__(self, coordinator: BasketTvCoordinator, slug: str, cfg: dict) -> None:
        super().__init__(coordinator)
        self._slug = slug
        self._display_name = cfg.get("name") or slug.replace("-", " ").title()
        self._attr_name = f"Basket {self._display_name}"
        self._attr_unique_id = f"baskettv_{slug.replace('-', '_')}"
        self._attr_icon = "mdi:basketball"

    @property
    def _data(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._slug)

    @property
    def native_value(self) -> str:
        d = self._data
        return d["state"] if d else "Aucun match"

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data
        if d is None:
            return {**EMPTY_ATTRS, "team": self._display_name, "slug": self._slug}
        return d.get("attributes", {})

    @property
    def device_info(self):
        # Un appareil par équipe
        return {
            "identifiers": {(DOMAIN, f"baskettv_{self._slug}")},
            "name": f"Basket TV {self._display_name}",
            "model": "Match Sensor",
            "manufacturer": "developpeurbox",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
