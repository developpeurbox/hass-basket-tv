"""Parseur du flux RSS d'une équipe sur tv-sports.fr (aucune dépendance HA)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

TAG_RE = re.compile(r"^\[(?P<tag>[^\]]+)\]\s*(?P<rest>.+)$")
SPORT_PREFIX_RE = re.compile(r"^Basket-ball\s*-\s*", re.I)
TEAM_SEP = " – "  # tiret demi-cadratin utilisé par le site

TAG_LIVE = "en direct"
TAG_REPLAY = "rediffusion"  # le site l'utilise aussi pour du streaming (DAZN)
TAG_UPCOMING = "match à venir"

MATCH_DURATION = timedelta(hours=3)  # le match reste affiché pendant qu'il se joue


@dataclass
class Match:
    home: str
    away: str
    competition: str
    start: datetime
    channels: list[str] = field(default_factory=list)
    link: str = ""


def _parse_item(item: ET.Element) -> dict | None:
    desc = (item.findtext("description") or "").split("\n")[0].strip()
    m = TAG_RE.match(desc)
    if not m:
        return None
    parts = [p.strip() for p in m.group("rest").split(" | ")]
    if len(parts) < 2 or TEAM_SEP not in parts[0]:
        return None
    home, away = (t.strip() for t in parts[0].split(TEAM_SEP, 1))
    pub = item.findtext("pubDate")
    if not pub:
        return None
    return {
        "tag": m.group("tag").strip().lower(),
        "home": home,
        "away": away,
        "competition": SPORT_PREFIX_RE.sub("", parts[1]),
        "channel": parts[2] if len(parts) > 2 and parts[2] else None,
        "when": parsedate_to_datetime(pub),
        "link": (item.findtext("link") or "").strip(),
    }


def parse_feed(xml_text: str, now: datetime | None = None,
               include_replays: bool = True) -> list[Match]:
    """Retourne les matchs télévisés/streamés à venir (ou en cours), triés par date.

    - « En direct » : match retransmis, avec la chaîne.
    - « Rediffusion » : gardé par défaut, car le site étiquette ainsi les matchs
      DAZN (indiqués « streaming » sur le site). include_replays=False les ignore.
    - « Match à venir » : pas de chaîne ; sert à donner l'heure du coup d'envoi
      quand le match est aussi retransmis (l'heure de diffusion peut différer).
    """
    now = now or datetime.now(timezone.utc)
    root = ET.fromstring(xml_text)
    groups: dict[tuple, dict] = {}

    for item in root.iter("item"):
        it = _parse_item(item)
        if not it:
            continue
        key = (it["home"].lower(), it["away"].lower(), it["when"].date())
        g = groups.setdefault(key, {"upcoming": None, "live": [], "replay": []})
        if it["tag"] == TAG_LIVE:
            g["live"].append(it)
        elif it["tag"] == TAG_REPLAY:
            g["replay"].append(it)
        elif it["tag"] == TAG_UPCOMING:
            g["upcoming"] = it

    matches: list[Match] = []
    for g in groups.values():
        casts = g["live"] + (g["replay"] if include_replays else [])
        if not casts:
            continue
        ref = g["upcoming"] or casts[0]
        channels: list[str] = []
        for c in casts:
            if c["channel"] and c["channel"] not in channels:
                channels.append(c["channel"])
        matches.append(Match(
            home=ref["home"], away=ref["away"], competition=ref["competition"],
            start=ref["when"], channels=channels, link=casts[0]["link"],
        ))

    matches = [m for m in matches if m.start + MATCH_DURATION > now]
    matches.sort(key=lambda m: m.start)
    return matches


def next_match(xml_text: str, **kw) -> Match | None:
    ms = parse_feed(xml_text, **kw)
    return ms[0] if ms else None
