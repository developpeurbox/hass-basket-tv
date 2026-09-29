"""Construction des données d'un sensor depuis le flux RSS (sans dépendance HA)."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from .parser import MATCH_DURATION, next_match

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def same_team(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or (min(len(na), len(nb)) >= 4 and (na in nb or nb in na))


def logo_for(name: str, team_name: str, team_logo: str, logos: dict[str, str]) -> str:
    """Logo d'une équipe : le club suivi, sinon un club connu du dataset, sinon vide."""
    if same_team(name, team_name):
        return team_logo
    n = norm(name)
    if n in logos:
        return logos[n]
    for key, url in logos.items():
        if same_team(key, n):
            return url
    return ""


def channel_logo(name: str, channels: dict[str, str]) -> str:
    """Logo d'une chaîne à partir de channels.json (nom normalisé -> URL)."""
    if not name:
        return ""
    return channels.get(norm(name), "")


def build_club_data(slug: str, cfg: dict, xml_text: str, logos: dict[str, str],
                    now: datetime, channels: dict[str, str] | None = None) -> dict:
    """Retourne {"state": ..., "attributes": {...}} pour un club."""
    team = cfg.get("name") or slug.replace("-", " ").title()
    team_logo = cfg.get("logo", "")
    m = next_match(xml_text, now=now)

    if m is None:
        return {
            "state": "Aucun match",
            "attributes": {"team": team, "logoTeam": team_logo, "competition": "", "slug": slug},
        }

    start = m.start.astimezone(now.tzinfo)
    fin = start + MATCH_DURATION
    situation = "dom" if same_team(m.home, team) else "ext"
    ch = m.channels
    channels = channels or {}

    return {
        "state": ch[0] if ch else "Non renseigné",
        "attributes": {
            "team": team,
            "logoTeam": team_logo,
            "competition": m.competition,
            "journee": "",
            "domicile": m.home,
            "logoDomicile": logo_for(m.home, team, team_logo, logos),
            "shortDomicile": m.home,
            "exterieur": m.away,
            "logoExterieur": logo_for(m.away, team, team_logo, logos),
            "shortExterieur": m.away,
            "situation": situation,
            "date": start.strftime("%d/%m/%Y"),
            "date_fr": f"{JOURS_FR[start.weekday()]} {start.day} {MOIS_FR[start.month - 1]} {start.year}",
            "datetime": start.strftime("%Y-%m-%d %H:%M:%S"),
            "datetime_fin": fin.strftime("%Y-%m-%d %H:%M:%S"),
            "display": fin > now,
            "heure": start.strftime("%H:%M"),
            "diffuseur1": ch[0] if ch else "",
            "logoDiffuseur1": channel_logo(ch[0], channels) if ch else "",
            "diffuseur2": ch[1] if len(ch) > 1 else "",
            "logoDiffuseur2": channel_logo(ch[1], channels) if len(ch) > 1 else "",
            "chaines": ch,
            "game": f"{m.home} - {m.away}",
            "lien_match": m.link,
            "slug": slug,

        },
    }
