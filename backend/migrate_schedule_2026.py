"""
Migration : corrige le calendrier (dates, heures, chaînes TV) des matchs de
phase de groupes déjà présents en base, pour qu'il corresponde au calendrier
RÉEL de la Coupe du Monde 2026 (désormais codé en dur dans
fixtures.REAL_SCHEDULE), SANS toucher aux pronostics existants (`id` et
équipes home/away conservés).

Contexte : les paires d'équipes (home/away) générées par
build_group_stage_matches() n'ont PAS changé par rapport à la version
précédente (seules les dates/heures/chaînes étaient fictives). On fait donc
correspondre chaque document existant à son nouveau fixture par IDENTITÉ DE
PAIRE D'ÉQUIPES (l'ensemble {home_team, away_team}) au sein du même
(group, matchday) - et non par tri sur kickoff_utc, qui peut donner un ordre
différent entre l'ancien calendrier (fictif) et le nouveau (réel).

Champs mis à jour : kickoff_utc, display_date, kickoff_hour_paris,
broadcast_channels.
Champs conservés : id, home_team, away_team, home_code, away_code, status,
home_score_actual, away_score_actual, phase, group, matchday.

Usage :
    python migrate_schedule_2026.py            # dry-run : affiche les changements
    python migrate_schedule_2026.py --apply     # applique réellement les changements
"""
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from pymongo import MongoClient

from fixtures import build_group_stage_matches

load_dotenv()

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def main():
    apply = "--apply" in sys.argv

    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    new_matches = build_group_stage_matches()

    # Regroupe les nouveaux fixtures par (group, matchday, {home, away})
    new_by_slot = defaultdict(dict)
    for m in new_matches:
        key = (m["group"], m["matchday"])
        pair = frozenset((m["home_team"], m["away_team"]))
        new_by_slot[key][pair] = m

    old_docs = list(db.matches.find({"phase": "group"}))
    if not old_docs:
        print("Aucun match de phase de groupes en base - rien à migrer "
              "(le seed initial appliquera directement le nouveau calendrier).")
        return

    total_updates = 0
    total_unchanged = 0
    warnings = []

    for old in old_docs:
        key = (old["group"], old["matchday"])
        pair = frozenset((old.get("home_team"), old.get("away_team")))

        new = new_by_slot.get(key, {}).get(pair)
        if not new:
            warnings.append(
                f"Groupe {old['group']} journée {old['matchday']} : aucune correspondance "
                f"trouvée pour {old.get('home_team')} vs {old.get('away_team')} "
                f"(id={old['id']}) - vérifier manuellement."
            )
            continue

        fields_to_update = {
            "kickoff_utc": new["kickoff_utc"],
            "display_date": new["display_date"],
            "kickoff_hour_paris": new["kickoff_hour_paris"],
            "broadcast_channels": new["broadcast_channels"],
        }

        if (
            old.get("kickoff_utc") == new["kickoff_utc"]
            and old.get("display_date") == new["display_date"]
            and old.get("kickoff_hour_paris") == new["kickoff_hour_paris"]
            and old.get("broadcast_channels") == new["broadcast_channels"]
        ):
            total_unchanged += 1
            continue

        total_updates += 1
        label = f"{old.get('home_team')} vs {old.get('away_team')}"
        print(
            f"[{key[0]} J{key[1]}] id={old['id']}: {label}  "
            f"{old.get('display_date')} {old.get('kickoff_hour_paris')}h "
            f"-> {new['display_date']} {new['kickoff_hour_paris']}h "
            f"({new['broadcast_channels']})"
        )

        if apply:
            db.matches.update_one({"id": old["id"]}, {"$set": fields_to_update})

    print()
    print(f"{total_updates} match(s) à mettre à jour, {total_unchanged} inchangé(s).")
    for w in warnings:
        print(f"ATTENTION: {w}")

    if not apply:
        print("\nDry-run : aucune modification appliquée. Relancer avec --apply pour écrire en base.")
    else:
        print("\nMigration appliquée.")


if __name__ == "__main__":
    main()
