<p align="center">
  <img src="/doc/images/example.png" alt="Exemple d'affichage" width="400"/>
</p>

# Basket TV — Intégration HACS pour Home Assistant
[![PayPal](https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&color=purple&logo=paypal&logoColor=ccc&link=https%3A%2F%2Fpaypal.me%2hlaissus/5)](https://paypal.me/hlaissus/5)
[![GitHub Release]( https://img.shields.io/github/v/release/developpeurbox/hass-basket-tv?style=for-the-badge&color=blue)](https://github.com/developpeurbox/hass-basket-tv/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&color=blue)](https://github.com/hacs/integration)
[![Community Forum]( https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge&color=pink)](https://forum.hacf.fr/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-basket-tv/blob/main/LICENSE)

[![HACS Action](https://github.com/developpeurbox/hass-basket-tv/actions/workflows/hacs.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-basket-tv/actions/workflows/hacs.yml)
[![HACS Action](https://github.com/developpeurbox/hass-basket-tv/actions/workflows/hassfest.yml/badge.svg?style=for-the-badge)](https://github.com/developpeurbox/hass-basket-tv/actions/workflows/hassfest.yml)

Intégration personnalisée pour Home Assistant permettant de suivre le **prochain match télévisé** de vos clubs de basket préférés (Betclic Élite, Pro B, Euroligue, NBA, équipes de France), à partir des flux RSS de
<p align="center">
<a class="site-name" href="https://tv-sports.fr/">
  <img class="site-mark" src="https://tv-sports.fr/assets/images/site-mark-a61ba04520fd.webp?v=1786886556"
       alt="Logo tv-sports.fr" width="96" height="96" aria-hidden="true">
  <span></span>
</a>
</p>

> 🎴 La carte Lovelace dédiée n'est **pas incluse** dans ce dépôt — elle vit dans son propre repo : [`ha-basket-tv-game-card`](https://github.com/developpeurbox/basket-tv-game-card), à installer séparément.

## ✨ Caractéristiques

- 📅 Suivi multi-clubs : un sensor par club, toutes compétitions confondues (championnat national **et** coupes européennes pour les clubs qui y jouent, ex. ASVEL en Euroligue).
- 📺 Infos complètes : adversaire, domicile/extérieur, compétition, date, heure, diffuseur(s) TV et leurs logos, logos des équipes.
- ⚙️ Configuration via l'interface Home Assistant (une équipe par entrée, ajoutez l'intégration autant de fois que nécessaire).
- 🔗 Lien direct vers la fiche du match sur tv-sports.fr.


## 📦 Installation

> [!TIP]
> ### Installation Rapide via HACS
> Cliquez sur le bouton ci-dessous pour ajouter automatiquement le dépôt dans HACS :
>
> [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=developpeurbox&repository=hass-basket-tv&category=integration)

### 🏗️ Méthode 1 : HACS (Recommandée)

   1. Ouvrez **HACS** dans Home Assistant
   2. Allez dans **Intégrations**
   3. Cliquez sur les **3 points** en haut à droite → **Dépôts personnalisés**
   4. Ajouter: [https://github.com/developpeurbox/hass-basket-tv.git](https://github.com/developpeurbox/hass-basket-tv)
   5. Catégorie **Integration**
   6. Cherchez "**Basket TV**" et cliquez sur **Télécharger**
   7. **Redémarrez Home Assistant**
   
### 🏗️ Méthode 2 : Manuelle
   1. Téléchargez le dossier `custom_components/basket_tv//` de ce dépôt.
   2. Copiez-le dans le dossier `custom_components/basket_tv//`  de votre instance Home Assistant.
   3. **Redémarrez Home Assistant**

## ⚙️ Configuration

> [!IMPORTANT]
> ### Configuration Rapide
> Cliquez sur le bouton ci-dessous pour démarrer la configuration automatiquement :
>
> [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=basket_tv)

### Configuration Manuelle

1. Allez dans **Configuration** → **Appareils et Services**
2. Cliquez sur **+ Ajouter une intégration**
3. Cherchez "**Basket TV**"
4. Renseignez les informations :

Les équipes se saisissent depuis l'UI au moment de l'ajout de l'intégration

## 🎴 Carte Lovelace

Voir [`ha-basket-tv-game-card`](https://github.com/developpeurbox/ha-basket-tv-game-card) pour l'installation (HACS "Frontend" ou manuelle + ressource Lovelace).
Une fois installée :

```yaml
type: custom:basket-tv-game-card
entity: sensor.basket_asvel
footer_bg: "rgba(0,0,0,0.45)"
footer_color: "#f77f00"
```

Pour afficher tous vos matchs :

```yaml
type: custom:auto-entities
card:
  type: entities
filter:
  include:
    - options:
        type: custom:basket-tv-game-card
      entity_id: sensor.basket_*
      sort:
        method: attribute
        attribute: datetime
```

## 🔁 Rafraîchissement

Les données sont mises à jour automatiquement **toutes les 12 heures**. Un rafraîchissement manuel est possible depuis l'UI de l'intégration.

## 🏀 Clubs suivis

Le fichier [`custom_components/basket_tv/clubs.json`](https://github.com/developpeurbox/hass-basket-tv/blob/main/custom_components/basket_tv/clubs.json) liste les clubs suivis, par compétition, avec leur identifiant tv-sports.fr et leur logo.

Pour ajouter un club, récupère son identifiant dans l'URL de son flux (`tv-sports.fr/rss/equipe/<code>/<slug>`) et ajoute-le dans `clubs.json`.

## 📡 Chaînes référencées

Le fichier [`custom_components/basket_tv/channels.json`](https://github.com/developpeurbox/hass-basket-tv/blob/main/custom_components/basket_tv/channels.json) associe le nom de chaque diffuseur (tel qu'il apparaît sur tv-sports.fr) à son logo. Une chaîne absente de ce fichier s'affiche quand même (son nom en texte), simplement sans logo — ajoute-la dans `channels.json` pour la compléter.

## ⚠️ Note importante sur la source des données

Cette intégration s'appuie sur les flux RSS publics par équipe de [**tv-sports.fr**](https://tv-sports.fr/) (`tv-sports.fr/rss/equipe/<code>/<slug>?direct=1`), qui listent les matchs de chaque club, toutes compétitions confondues, avec la chaîne de diffusion. Elle n'effectue aucun scraping de page HTML. Si le format du flux venait à changer, c'est `parser.py` qu'il faut corriger — active les logs `debug` du composant `basket_tv` en cas de sensor vide ou d'erreur :

```yaml
logger:
  default: warning
  logs:
    custom_components.basket_tv: debug
```

---

*Toutes les données de match et de diffusion proviennent de [tv-sports.fr](https://tv-sports.fr/). Merci de garder un usage personnel et un intervalle de rafraîchissement raisonnable.*


## 💬 **Communauté & Support**
🗣️ **Forum Home Assistant** : [Discuter ici](https://forum.hacf.fr/t/carte-lovelace-integration-basket-tv-le-programme-tv-arrive-dans-home-assistant/84193)


## 🔧 Attributs disponibles par sensor

**Attributs**

| Attribut                        | Description                                                        |
| -------------------------------- | ------------------------------------------------------------------- |
| `state`                          | Nom du diffuseur TV principal (ex: beIN SPORTS 1), ou "Aucun match" |
| `team`                            | Nom complet du club suivi                                           |
| `logoTeam`                        | URL du logo du club suivi                                           |
| `competition`                     | Compétition du prochain match (ex: Betclic Élite, Euroligue)        |
| `domicile`                        | Équipe à domicile                                                    |
| `logoDomicile`                    | Logo de l'équipe à domicile                                          |
| `exterieur`                       | Équipe à l'extérieur                                                 |
| `logoExterieur`                   | Logo de l'équipe à l'extérieur                                       |
| `situation`                       | `dom` ou `ext` selon le rôle du club suivi                          |
| `date` / `date_fr`                | Date brute (JJ/MM/AAAA) / date en français                          |
| `datetime` / `datetime_fin`       | Horodatage ISO du coup d'envoi / fin estimée                        |
| `display`                         | `true` si le match est dans le futur                                |
| `heure`                           | Heure du coup d'envoi (HH:MM)                                       |
| `diffuseur1` / `logoDiffuseur1`   | Nom / logo du 1er diffuseur TV                                      |
| `diffuseur2` / `logoDiffuseur2`   | Nom / logo du 2e diffuseur TV (s'il y en a un)                      |
| `chaines`                         | Liste de tous les diffuseurs du match                               |
| `game`                            | Texte "Domicile - Extérieur"                                        |
| `lien_match`                      | URL de la fiche du match sur tv-sports.fr                           |

