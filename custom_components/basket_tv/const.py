"""Constantes pour l'intégration Basket TV (Betclic Élite / Pro B / NBA)."""

DOMAIN = "basket_tv"
SCAN_INTERVAL_HOURS = 12  # le flux RSS annonce lui-même un ttl de 6 h

# Flux RSS par équipe (code numérique + slug), limité aux matchs retransmis
RSS_URL = "https://tv-sports.fr/rss/equipe/{code}/{slug}?direct=1"
REQUEST_DELAY = 2  # secondes entre deux clubs, pour rester poli avec le site

# URL distante du fichier clubs.json (liste des clubs par championnat).
CLUBS_JSON_URL = (
    "https://raw.githubusercontent.com/developpeurbox/hass-basket-tv/"
    "refs/heads/main/custom_components/basket_tv/clubs.json"
)
CLUBS_CACHE_TTL = 3600  # secondes — rechargement max 1x/heure

# URL distante du fichier channels.json (logo des chaînes de diffusion).
CHANNELS_JSON_URL = (
    "https://raw.githubusercontent.com/developpeurbox/hass-basket-tv/"
    "refs/heads/main/custom_components/basket_tv/channels.json"
)
