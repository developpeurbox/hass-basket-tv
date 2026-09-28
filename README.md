# Basket TV — Betclic Élite / Pro B / NBA

Intégration Home Assistant (HACS) qui donne, pour chaque club suivi, le **prochain match diffusé** (chaîne, heure, adversaire, logos). Même principe que [hass-rugby-tv](https://github.com/developpeurbox/hass-rugby-tv), avec le flux RSS par équipe de tv-sports.fr.

## Installation
1. HACS → Dépôts personnalisés → ajouter ce dépôt (catégorie *Intégration*).
2. Installer **Basket TV**, redémarrer Home Assistant.
3. Paramètres → Appareils et services → Ajouter une intégration → **Basket TV**, puis cocher les clubs.
   Une seule instance est autorisée ; les clubs se modifient via *Configurer*.

## Fonctionnement
- Un capteur par club : `sensor.basket_<club>`, état = chaîne du prochain match diffusé (ou `Aucun match`).
- Source : `https://tv-sports.fr/rss/equipe/<code>/<slug>?direct=1` (le club, toutes compétitions : championnat, Euroligue…).
- On garde les items **« En direct »** et **« Rediffusion »** : tv-sports.fr étiquette ainsi les matchs en streaming (DAZN). Les « Match à venir » sans chaîne sont ignorés, mais donnent l'heure exacte du coup d'envoi.
- Une seule chaîne est lue (celle du flux). Si le flux en liste plusieurs, elles sont dans `chaines`, `diffuseur1` et `diffuseur2`.
- Rafraîchissement toutes les 6 h, 1,5 s entre deux clubs. Le dernier état connu est conservé si le site ne répond pas.
- Le match reste affiché 3 h après le coup d'envoi.

## Attributs
`team`, `logoTeam`, `competition`, `domicile`, `logoDomicile`, `exterieur`, `logoExterieur`, `situation` (`dom`/`ext`), `date`, `date_fr`, `heure`, `datetime`, `datetime_fin`, `display`, `diffuseur1`, `diffuseur2`, `chaines`, `game`, `lien_match`, `slug`.
Les logos des adversaires ne sont fournis que pour les clubs du dataset (France, NBA, Euroligue) ; un club absent du fichier s’affiche sans logo.

## Clubs
`custom_components/basket_tv/clubs.json` : 83 équipes (16 Betclic Élite, 19 Pro B, 30 NBA, 16 Euroligue, 2 équipes de France), avec `code` (identifiant tv-sports.fr) et logo. Pour ajouter un club, il suffit d'ajouter son slug et son code (visible dans l'URL du flux).

Données : tv-sports.fr — usage personnel, merci de garder un rafraîchissement raisonnable.
