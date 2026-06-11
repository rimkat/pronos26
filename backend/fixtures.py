"""
Calendrier officiel-like de la Coupe du Monde 2026.
Format 48 équipes, 12 groupes (A-L), 4 équipes/groupe, 3 journées.
Tournoi du 11 juin au 19 juillet 2026 (USA/Mexique/Canada).

Chaque équipe : { name, code } où code est utilisé par flagcdn.com.
"""
from datetime import datetime, timezone, timedelta

# 48 équipes réparties en 12 groupes - tirage au sort officiel de la
# Coupe du Monde 2026 (Canada/Mexique/États-Unis)
GROUPS = {
    "A": [
        {"name": "Mexique", "code": "mx"},
        {"name": "Afrique du Sud", "code": "za"},
        {"name": "Corée du Sud", "code": "kr"},
        {"name": "Tchéquie", "code": "cz"},
    ],
    "B": [
        {"name": "Canada", "code": "ca"},
        {"name": "Bosnie-Herzégovine", "code": "ba"},
        {"name": "Qatar", "code": "qa"},
        {"name": "Suisse", "code": "ch"},
    ],
    "C": [
        {"name": "Brésil", "code": "br"},
        {"name": "Maroc", "code": "ma"},
        {"name": "Haïti", "code": "ht"},
        {"name": "Écosse", "code": "gb-sct"},
    ],
    "D": [
        {"name": "États-Unis", "code": "us"},
        {"name": "Paraguay", "code": "py"},
        {"name": "Australie", "code": "au"},
        {"name": "Turquie", "code": "tr"},
    ],
    "E": [
        {"name": "Allemagne", "code": "de"},
        {"name": "Curaçao", "code": "cw"},
        {"name": "Côte d'Ivoire", "code": "ci"},
        {"name": "Équateur", "code": "ec"},
    ],
    "F": [
        {"name": "Pays-Bas", "code": "nl"},
        {"name": "Japon", "code": "jp"},
        {"name": "Suède", "code": "se"},
        {"name": "Tunisie", "code": "tn"},
    ],
    "G": [
        {"name": "Belgique", "code": "be"},
        {"name": "Égypte", "code": "eg"},
        {"name": "Iran", "code": "ir"},
        {"name": "Nouvelle-Zélande", "code": "nz"},
    ],
    "H": [
        {"name": "Espagne", "code": "es"},
        {"name": "Cap-Vert", "code": "cv"},
        {"name": "Arabie saoudite", "code": "sa"},
        {"name": "Uruguay", "code": "uy"},
    ],
    "I": [
        {"name": "France", "code": "fr"},
        {"name": "Sénégal", "code": "sn"},
        {"name": "Irak", "code": "iq"},
        {"name": "Norvège", "code": "no"},
    ],
    "J": [
        {"name": "Argentine", "code": "ar"},
        {"name": "Algérie", "code": "dz"},
        {"name": "Autriche", "code": "at"},
        {"name": "Jordanie", "code": "jo"},
    ],
    "K": [
        {"name": "Portugal", "code": "pt"},
        {"name": "RD Congo", "code": "cd"},
        {"name": "Ouzbékistan", "code": "uz"},
        {"name": "Colombie", "code": "co"},
    ],
    "L": [
        {"name": "Angleterre", "code": "gb-eng"},
        {"name": "Croatie", "code": "hr"},
        {"name": "Ghana", "code": "gh"},
        {"name": "Panama", "code": "pa"},
    ],
}

# Chaînes TV de diffusion (cycle réaliste)
TV_CHANNELS_CYCLE = [
    "beIN Sports 1, TF1",
    "beIN Sports 1, M6",
    "beIN Sports 2",
    "beIN Sports 1",
    "beIN Sports 3, M6",
    "beIN Sports 1, TF1",
]

# Heures de coup d'envoi (en heure de Paris, format 24h)
KICKOFF_HOURS = [18, 21, 0, 3]  # 18h, 21h, minuit, 3h du matin


def _utc_from_paris(date_str: str, hour: int) -> str:
    """Convertit date Paris + heure -> ISO UTC. Juin = UTC+2."""
    # date_str: "2026-06-11", hour: 21 (heure de Paris)
    dt_paris = datetime.fromisoformat(date_str + f"T{hour:02d}:00:00")
    dt_utc = dt_paris - timedelta(hours=2)
    return dt_utc.replace(tzinfo=timezone.utc).isoformat()


def build_group_stage_matches() -> list[dict]:
    """
    Génère les 72 matchs de phase de groupes.
    3 journées par groupe, calendrier étalé du 11 au 26 juin 2026.
    """
    matches = []
    # Programme des journées (4 équipes : 1v2, 3v4 / 1v3, 4v2 / 4v1, 2v3)
    matchday_pairs = [
        [(0, 1), (2, 3)],
        [(0, 2), (3, 1)],
        [(3, 0), (1, 2)],
    ]

    # Dates : phase de groupes du 11 juin au 26 juin (16 jours)
    # 12 groupes * 3 journées = 36 "blocs", on étale sur les jours
    base_date = datetime(2026, 6, 11)
    group_list = list(GROUPS.keys())

    counter = 0
    for md_index in range(3):  # journée 1, 2, 3
        for g_index, group in enumerate(group_list):
            teams = GROUPS[group]
            for pair_index, (i, j) in enumerate(matchday_pairs[md_index]):
                day_offset = (md_index * 5) + (g_index // 3)
                match_date = base_date + timedelta(days=day_offset)
                date_str = match_date.strftime("%Y-%m-%d")
                hour = KICKOFF_HOURS[counter % len(KICKOFF_HOURS)]
                tv = TV_CHANNELS_CYCLE[counter % len(TV_CHANNELS_CYCLE)]

                # Pour les matchs à 00h ou 03h, ils ont lieu le lendemain en heure locale
                # mais on les classe au jour calendaire de la date Paris
                if hour < 6:
                    display_date = (match_date + timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    display_date = date_str

                matches.append({
                    "home_team": teams[i]["name"],
                    "home_code": teams[i]["code"],
                    "away_team": teams[j]["name"],
                    "away_code": teams[j]["code"],
                    "group": group,
                    "matchday": md_index + 1,
                    "kickoff_utc": _utc_from_paris(date_str, hour),
                    "display_date": display_date,
                    "kickoff_hour_paris": hour,
                    "broadcast_channels": tv,
                    "status": "scheduled",
                    "home_score_actual": None,
                    "away_score_actual": None,
                })
                counter += 1

    # On force les 3 affiches du brief à des valeurs précises
    _force_brief_matches(matches)
    # Ajoute phase="group" sur chaque match
    for m in matches:
        m["phase"] = "group"
        m["round"] = None
    return matches


# ------------------------------------------------------------------
# Phase à élimination directe (placeholders)
# ------------------------------------------------------------------

KNOCKOUT_ROUNDS = [
    # (round_key, label, nb_matches, date_start_offset, daily_count)
    ("R32", "1/16 de finale", 16, 16),   # 27 juin -> +16 jours après 11 juin
    ("R16", "1/8 de finale", 8, 22),     # 3 juillet
    ("QF",  "1/4 de finale", 4, 28),     # 9 juillet
    ("SF",  "1/2 finale",     2, 33),    # 14 juillet
    ("3RD", "Match pour la 3e place", 1, 37),  # 18 juillet
    ("F",   "Finale",         1, 38),    # 19 juillet
]


def build_knockout_matches() -> list[dict]:
    """
    Génère 32 matchs placeholders pour la phase à élimination directe.
    Les équipes sont 'TBD' et seront mises à jour lorsque la phase de groupes sera terminée.
    """
    matches = []
    base = datetime(2026, 6, 11)

    for round_key, label, nb, date_offset in KNOCKOUT_ROUNDS:
        for i in range(nb):
            day = base + timedelta(days=date_offset + (i // 2))
            hour = 21 if i % 2 == 0 else 0
            display_day = day if hour >= 6 else day + timedelta(days=0)
            display_date = display_day.strftime("%Y-%m-%d")
            kickoff_str = _utc_from_paris(day.strftime("%Y-%m-%d"), hour)
            matches.append({
                "home_team": f"À déterminer",
                "home_code": "",
                "away_team": f"À déterminer",
                "away_code": "",
                "group": round_key,
                "matchday": i + 1,
                "kickoff_utc": kickoff_str,
                "display_date": display_date,
                "kickoff_hour_paris": hour,
                "broadcast_channels": "beIN Sports 1, TF1" if round_key in ("SF", "F", "3RD") else "beIN Sports 1",
                "status": "scheduled",
                "home_score_actual": None,
                "away_score_actual": None,
                "phase": "knockout",
                "round": round_key,
                "round_label": label,
            })
    return matches


def _force_brief_matches(matches: list[dict]):
    """Aligne les 3 affiches mentionnées dans le cahier des charges."""
    # Qatar vs Suisse - Groupe B - 21h00 - beIN Sports 1, M6
    for m in matches:
        if m["group"] == "B" and {m["home_team"], m["away_team"]} == {"Qatar", "Suisse"}:
            m["kickoff_hour_paris"] = 21
            m["broadcast_channels"] = "beIN Sports 1, M6"
            # Recalcul UTC
            dt_paris = datetime.fromisoformat("2026-06-12T21:00:00")
            m["kickoff_utc"] = (dt_paris - timedelta(hours=2)).replace(tzinfo=timezone.utc).isoformat()
            m["display_date"] = "2026-06-12"
            break

    # Brésil vs Maroc - Groupe C - dim. 00h00 - beIN Sports 1, M6
    for m in matches:
        if m["group"] == "C" and {m["home_team"], m["away_team"]} == {"Brésil", "Maroc"}:
            m["kickoff_hour_paris"] = 0
            m["broadcast_channels"] = "beIN Sports 1, M6"
            # 00h00 dimanche heure Paris = samedi 22h UTC
            dt_paris = datetime.fromisoformat("2026-06-14T00:00:00")
            m["kickoff_utc"] = (dt_paris - timedelta(hours=2)).replace(tzinfo=timezone.utc).isoformat()
            m["display_date"] = "2026-06-14"
            break

    # Haïti vs Écosse - Groupe C - dim. 03h00 - beIN Sports 1
    for m in matches:
        if m["group"] == "C" and {m["home_team"], m["away_team"]} == {"Haïti", "Écosse"}:
            m["kickoff_hour_paris"] = 3
            m["broadcast_channels"] = "beIN Sports 1"
            dt_paris = datetime.fromisoformat("2026-06-14T03:00:00")
            m["kickoff_utc"] = (dt_paris - timedelta(hours=2)).replace(tzinfo=timezone.utc).isoformat()
            m["display_date"] = "2026-06-14"
            break
