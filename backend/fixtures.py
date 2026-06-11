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


