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

def _utc_from_paris(date_str: str, hour: int, minute: int = 0) -> str:
    """Convertit date Paris + heure -> ISO UTC. Juin = UTC+2 (heure d'été)."""
    # date_str: "2026-06-11", hour: 21 (heure de Paris)
    dt_paris = datetime.fromisoformat(date_str + f"T{hour:02d}:{minute:02d}:00")
    dt_utc = dt_paris - timedelta(hours=2)
    return dt_utc.replace(tzinfo=timezone.utc).isoformat()


# ------------------------------------------------------------------
# Calendrier réel de la phase de groupes (Coupe du Monde 2026)
# Source : footmercato.net - calendrier officiel par groupe.
# Pour chaque groupe : 3 journées, chacune composée de 2 matchs
# (home, away, date Paris "YYYY-MM-DD", heure Paris, minute, chaînes TV).
# Les dates/heures sont celles affichées en heure de Paris.
# ------------------------------------------------------------------
REAL_SCHEDULE: dict[str, list[list[tuple]]] = {
    "A": [
        [
            ("Mexique", "Afrique du Sud", "2026-06-11", 21, 0, "beIN Sports 1, M6"),
            ("Corée du Sud", "Tchéquie", "2026-06-12", 4, 0, "beIN Sports 1"),
        ],
        [
            ("Tchéquie", "Afrique du Sud", "2026-06-18", 18, 0, "beIN Sports 1, M6"),
            ("Mexique", "Corée du Sud", "2026-06-19", 3, 0, "beIN Sports 1"),
        ],
        [
            ("Tchéquie", "Mexique", "2026-06-25", 3, 0, "beIN Sports 1"),
            ("Afrique du Sud", "Corée du Sud", "2026-06-25", 3, 0, "beIN Sports 2"),
        ],
    ],
    "B": [
        [
            ("Canada", "Bosnie-Herzégovine", "2026-06-12", 21, 0, "beIN Sports 1, M6"),
            ("Qatar", "Suisse", "2026-06-13", 21, 0, "beIN Sports 1, M6"),
        ],
        [
            ("Suisse", "Bosnie-Herzégovine", "2026-06-18", 21, 0, "beIN Sports 1, M6"),
            ("Canada", "Qatar", "2026-06-19", 0, 0, "beIN Sports 1"),
        ],
        [
            ("Bosnie-Herzégovine", "Qatar", "2026-06-24", 21, 0, "beIN Sports 2"),
            ("Suisse", "Canada", "2026-06-24", 21, 0, "beIN Sports 1, M6"),
        ],
    ],
    "C": [
        [
            ("Brésil", "Maroc", "2026-06-14", 0, 0, "beIN Sports 1, M6"),
            ("Haïti", "Écosse", "2026-06-14", 3, 0, "beIN Sports 1"),
        ],
        [
            ("Écosse", "Maroc", "2026-06-20", 0, 0, "beIN Sports 1, M6"),
            ("Brésil", "Haïti", "2026-06-20", 2, 30, "beIN Sports 1"),
        ],
        [
            ("Maroc", "Haïti", "2026-06-25", 0, 0, "beIN Sports 2"),
            ("Écosse", "Brésil", "2026-06-25", 0, 0, "beIN Sports 1, M6"),
        ],
    ],
    "D": [
        [
            ("États-Unis", "Paraguay", "2026-06-13", 3, 0, "beIN Sports 1"),
            ("Australie", "Turquie", "2026-06-14", 6, 0, "beIN Sports 1"),
        ],
        [
            ("États-Unis", "Australie", "2026-06-19", 21, 0, "beIN Sports 1, M6"),
            ("Turquie", "Paraguay", "2026-06-20", 5, 0, "beIN Sports 1"),
        ],
        [
            ("Turquie", "États-Unis", "2026-06-26", 4, 0, "beIN Sports 1"),
            ("Paraguay", "Australie", "2026-06-26", 4, 0, "beIN Sports 2"),
        ],
    ],
    "E": [
        [
            ("Allemagne", "Curaçao", "2026-06-14", 19, 0, "beIN Sports 1, M6"),
            ("Côte d'Ivoire", "Équateur", "2026-06-15", 1, 0, "beIN Sports 1"),
        ],
        [
            ("Allemagne", "Côte d'Ivoire", "2026-06-20", 22, 0, "beIN Sports 1, M6"),
            ("Équateur", "Curaçao", "2026-06-21", 2, 0, "beIN Sports 1"),
        ],
        [
            ("Curaçao", "Côte d'Ivoire", "2026-06-25", 22, 0, "beIN Sports 2"),
            ("Équateur", "Allemagne", "2026-06-25", 22, 0, "beIN Sports 1, M6"),
        ],
    ],
    "F": [
        [
            ("Pays-Bas", "Japon", "2026-06-14", 22, 0, "beIN Sports 1, M6"),
            ("Suède", "Tunisie", "2026-06-15", 4, 0, "beIN Sports 1"),
        ],
        [
            ("Pays-Bas", "Suède", "2026-06-20", 19, 0, "beIN Sports 1, M6"),
            ("Tunisie", "Japon", "2026-06-21", 6, 0, "beIN Sports 1"),
        ],
        [
            ("Japon", "Suède", "2026-06-26", 1, 0, "beIN Sports 2"),
            ("Tunisie", "Pays-Bas", "2026-06-26", 1, 0, "beIN Sports 1, M6"),
        ],
    ],
    "G": [
        [
            ("Belgique", "Égypte", "2026-06-15", 21, 0, "beIN Sports 1, M6"),
            ("Iran", "Nouvelle-Zélande", "2026-06-16", 3, 0, "beIN Sports 1"),
        ],
        [
            ("Belgique", "Iran", "2026-06-21", 21, 0, "beIN Sports 1, M6"),
            ("Nouvelle-Zélande", "Égypte", "2026-06-22", 3, 0, "beIN Sports 1"),
        ],
        [
            ("Égypte", "Iran", "2026-06-27", 5, 0, "beIN Sports 2"),
            ("Nouvelle-Zélande", "Belgique", "2026-06-27", 5, 0, "beIN Sports 1"),
        ],
    ],
    "H": [
        [
            ("Espagne", "Cap-Vert", "2026-06-15", 18, 0, "beIN Sports 1, M6"),
            ("Arabie saoudite", "Uruguay", "2026-06-16", 0, 0, "beIN Sports 1, M6"),
        ],
        [
            ("Espagne", "Arabie saoudite", "2026-06-21", 18, 0, "beIN Sports 1, M6"),
            ("Uruguay", "Cap-Vert", "2026-06-22", 0, 0, "beIN Sports 1"),
        ],
        [
            ("Uruguay", "Espagne", "2026-06-27", 2, 0, "beIN Sports 1"),
            ("Cap-Vert", "Arabie saoudite", "2026-06-27", 2, 0, "beIN Sports 2"),
        ],
    ],
    "I": [
        [
            ("France", "Sénégal", "2026-06-16", 21, 0, "beIN Sports 1, M6"),
            ("Irak", "Norvège", "2026-06-17", 0, 0, "beIN Sports 1, M6"),
        ],
        [
            ("France", "Irak", "2026-06-22", 23, 0, "beIN Sports 1, M6"),
            ("Norvège", "Sénégal", "2026-06-23", 2, 0, "beIN Sports 1"),
        ],
        [
            ("Sénégal", "Irak", "2026-06-26", 21, 0, "beIN Sports 2"),
            ("Norvège", "France", "2026-06-26", 21, 0, "beIN Sports 1, M6"),
        ],
    ],
    "J": [
        [
            ("Argentine", "Algérie", "2026-06-17", 3, 0, "beIN Sports 1"),
            ("Autriche", "Jordanie", "2026-06-17", 6, 0, "beIN Sports 1"),
        ],
        [
            ("Argentine", "Autriche", "2026-06-22", 19, 0, "beIN Sports 1, M6"),
            ("Jordanie", "Algérie", "2026-06-23", 5, 0, "beIN Sports 1"),
        ],
        [
            ("Jordanie", "Argentine", "2026-06-28", 4, 0, "beIN Sports 2"),
            ("Algérie", "Autriche", "2026-06-28", 4, 0, "beIN Sports 1"),
        ],
    ],
    "K": [
        [
            ("Portugal", "RD Congo", "2026-06-17", 19, 0, "beIN Sports 1, M6"),
            ("Ouzbékistan", "Colombie", "2026-06-18", 4, 0, "beIN Sports 1"),
        ],
        [
            ("Portugal", "Ouzbékistan", "2026-06-23", 19, 0, "beIN Sports 1, M6"),
            ("Colombie", "RD Congo", "2026-06-24", 4, 0, "beIN Sports 1"),
        ],
        [
            ("Colombie", "Portugal", "2026-06-28", 1, 30, "beIN Sports 1, M6"),
            ("RD Congo", "Ouzbékistan", "2026-06-28", 1, 30, "beIN Sports 2"),
        ],
    ],
    "L": [
        [
            ("Angleterre", "Croatie", "2026-06-17", 22, 0, "beIN Sports 1, M6"),
            ("Ghana", "Panama", "2026-06-18", 1, 0, "beIN Sports 1"),
        ],
        [
            ("Angleterre", "Ghana", "2026-06-23", 22, 0, "beIN Sports 1, M6"),
            ("Panama", "Croatie", "2026-06-24", 1, 0, "beIN Sports 1"),
        ],
        [
            ("Panama", "Angleterre", "2026-06-27", 23, 0, "beIN Sports 1, M6"),
            ("Croatie", "Ghana", "2026-06-27", 23, 0, "beIN Sports 2"),
        ],
    ],
}


def build_group_stage_matches() -> list[dict]:
    """
    Génère les 72 matchs de phase de groupes à partir du calendrier réel
    (REAL_SCHEDULE), basé sur le calendrier officiel de la Coupe du Monde 2026.
    """
    matches = []

    for group, teams in GROUPS.items():
        team_by_name = {t["name"]: t for t in teams}
        schedule = REAL_SCHEDULE.get(group)
        if not schedule:
            continue

        for md_index, pairs in enumerate(schedule):
            for home_name, away_name, date_str, hour, minute, tv in pairs:
                home = team_by_name[home_name]
                away = team_by_name[away_name]

                matches.append({
                    "home_team": home["name"],
                    "home_code": home["code"],
                    "away_team": away["name"],
                    "away_code": away["code"],
                    "group": group,
                    "matchday": md_index + 1,
                    "kickoff_utc": _utc_from_paris(date_str, hour, minute),
                    "display_date": date_str,
                    "kickoff_hour_paris": hour,
                    "broadcast_channels": tv,
                    "status": "scheduled",
                    "home_score_actual": None,
                    "away_score_actual": None,
                })

    # Ajoute phase="group" sur chaque match
    for m in matches:
        m["phase"] = "group"
        m["round"] = None
    return matches


# ------------------------------------------------------------------
# Phase à élimination directe (placeholders) — calendrier RÉEL officiel
# Coupe du Monde 2026. Source : calendrier officiel FIFA (heures Paris).
# Chaque entrée : (matchday, date "YYYY-MM-DD", heure Paris, minute, ville)
# ------------------------------------------------------------------
REAL_KNOCKOUT_SCHEDULE: dict[str, list[tuple]] = {
    "R32": [
        (1, "2026-06-29", 22, 30, "Foxborough"),
        (2, "2026-06-30", 23, 0, "East Rutherford"),
        (3, "2026-06-28", 21, 0, "Los Angeles"),
        (4, "2026-06-30", 3, 0, "Monterrey"),
        (5, "2026-07-03", 1, 0, "Toronto"),
        (6, "2026-07-02", 21, 0, "Los Angeles"),
        (7, "2026-07-02", 2, 0, "Santa Clara"),
        (8, "2026-07-01", 22, 0, "Seattle"),
        (9, "2026-06-29", 19, 0, "Houston"),
        (10, "2026-06-30", 19, 0, "Arlington"),
        (11, "2026-07-01", 3, 0, "Mexico"),
        (12, "2026-07-01", 18, 0, "Atlanta"),
        (13, "2026-07-04", 0, 0, "Miami"),
        (14, "2026-07-03", 20, 0, "Arlington"),
        (15, "2026-07-03", 5, 0, "Vancouver"),
        (16, "2026-07-04", 3, 30, "Kansas City"),
    ],
    "R16": [
        (1, "2026-07-04", 23, 0, "Philadelphie"),
        (2, "2026-07-04", 19, 0, "Houston"),
        (3, "2026-07-06", 21, 0, "Arlington"),
        (4, "2026-07-07", 2, 0, "Seattle"),
        (5, "2026-07-05", 22, 0, "East Rutherford"),
        (6, "2026-07-06", 2, 0, "Mexico"),
        (7, "2026-07-07", 18, 0, "Atlanta"),
        (8, "2026-07-07", 22, 0, "Vancouver"),
    ],
    "QF": [
        (1, "2026-07-09", 22, 0, "Foxborough"),
        (2, "2026-07-10", 21, 0, "Los Angeles"),
        (3, "2026-07-11", 23, 0, "Miami"),
        (4, "2026-07-12", 3, 0, "Kansas City"),
    ],
    "SF": [
        (1, "2026-07-14", 21, 0, "Arlington"),
        (2, "2026-07-15", 21, 0, "Atlanta"),
    ],
    "3RD": [
        (1, "2026-07-18", 23, 0, "Miami"),
    ],
    "F": [
        (1, "2026-07-19", 21, 0, "East Rutherford"),
    ],
}

KNOCKOUT_ROUND_LABELS = {
    "R32": "1/16 de finale",
    "R16": "1/8 de finale",
    "QF": "1/4 de finale",
    "SF": "1/2 finale",
    "3RD": "Match pour la 3e place",
    "F": "Finale",
}


def build_knockout_matches() -> list[dict]:
    """
    Génère les matchs placeholders pour la phase à élimination directe,
    avec les VRAIES dates/heures/villes du calendrier officiel FIFA 2026.
    Les équipes sont 'À déterminer' et seront mises à jour au fil du tournoi
    (1ers/2es de groupe -> R32 manuellement, puis propagation automatique
    R32 -> R16 -> QF -> SF -> F/3RD via propagate_knockout_winner).
    """
    matches = []

    for round_key, entries in REAL_KNOCKOUT_SCHEDULE.items():
        label = KNOCKOUT_ROUND_LABELS[round_key]
        for matchday, date_str, hour, minute, city in entries:
            kickoff_str = _utc_from_paris(date_str, hour, minute)
            matches.append({
                "home_team": "À déterminer",
                "home_code": "",
                "away_team": "À déterminer",
                "away_code": "",
                "group": round_key,
                "matchday": matchday,
                "kickoff_utc": kickoff_str,
                "display_date": date_str,
                "kickoff_hour_paris": hour,
                "venue_city": city,
                "broadcast_channels": "beIN Sports 1, M6" if round_key in ("SF", "F", "3RD") else "beIN Sports 1",
                "status": "scheduled",
                "home_score_actual": None,
                "away_score_actual": None,
                "phase": "knockout",
                "round": round_key,
                "round_label": label,
            })
    return matches


