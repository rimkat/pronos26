"""
Migration : applique le nouveau tirage au sort (GROUPS dans fixtures.py) aux
matchs de phase de groupes déjà présents en base, SANS supprimer les
documents (et donc sans casser les pronostics existants, qui référencent
`match_id`).

Principe :
- `build_group_stage_matches()` génère les 72 matchs de phase de groupes dans
  un ordre déterministe : pour chaque journée (1-3), pour chaque groupe
  (A-L), 2 matchs (pair_index 0 et 1). Cet ordre/algorithme n'a PAS changé,
  seuls les noms d'équipes (GROUPS) ont changé. Le calendrier (dates, heures,
  chaînes TV) de chaque "slot" (groupe, journée, pair_index) reste donc
  identique entre l'ancien et le nouveau tirage.
- Pour chaque (groupe, journée), on récupère les documents existants en base
  et les nouveaux fixtures générés, on les trie par kickoff_utc (donne
  pair_index 0/1 de façon stable des deux côtés), puis on les associe 1:1.
- On met à jour : home_team, home_code, away_team, away_code, kickoff_utc,
  display_date, kickoff_hour_paris, broadcast_channels.
- On conserve : `id` (donc les pronostics restent valides), `phase`, `group`,
  `matchday`.
- On réinitialise : status="scheduled", home_score_actual/away_score_actual
  = None, winner_side supprimé si présent (puisque les équipes du match
  changent, un score précédent n'a plus de sens).

La phase à élimination directe (knockout) n'est PAS touchée : les équipes y
sont toujours "À déterminer" tant que la phase de groupes n'est pas terminée.

Usage :
    python migrate_groups_2026.py            # dry-run : affiche les changements
    python migrate_groups_2026.py --apply     # applique réellement les changements
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

    # Regroupe les nouveaux fixtures par (group, matchday), triés par kickoff_utc
    new_by_slot = defaultdict(list)
    for m in new_matches:
        new_by_slot[(m["group"], m["matchday"])].append(m)
    for key in new_by_slot:
        new_by_slot[key].sort(key=lambda m: m["kickoff_utc"])

    old_docs = list(db.matches.find({"phase": "group"}))
    if not old_docs:
        print("Aucun match de phase de groupes en base - rien à migrer "
              "(le seed initial appliquera directement le nouveau tirage).")
        return

    old_by_slot = defaultdict(list)
    for d in old_docs:
        old_by_slot[(d["group"], d["matchday"])].append(d)
    for key in old_by_slot:
        old_by_slot[key].sort(key=lambda d: d["kickoff_utc"])

    total_updates = 0
    total_unchanged = 0
    warnings = []

    all_slots = set(old_by_slot.keys()) | set(new_by_slot.keys())
    for slot in sorted(all_slots):
        olds = old_by_slot.get(slot, [])
        news = new_by_slot.get(slot, [])
        if len(olds) != len(news):
            warnings.append(
                f"Groupe {slot[0]} journée {slot[1]} : {len(olds)} match(s) en base "
                f"vs {len(news)} attendu(s) - vérifier manuellement."
            )

        for old, new in zip(olds, news):
            fields_to_update = {
                "home_team": new["home_team"],
                "home_code": new["home_code"],
                "away_team": new["away_team"],
                "away_code": new["away_code"],
                "kickoff_utc": new["kickoff_utc"],
                "display_date": new["display_date"],
                "kickoff_hour_paris": new["kickoff_hour_paris"],
                "broadcast_channels": new["broadcast_channels"],
            }

            same_teams = (
                old.get("home_team") == new["home_team"]
                and old.get("away_team") == new["away_team"]
            )

            unset_fields = {}
            if not same_teams:
                fields_to_update["status"] = "scheduled"
                fields_to_update["home_score_actual"] = None
                fields_to_update["away_score_actual"] = None
                if "winner_side" in old:
                    unset_fields["winner_side"] = ""

            if same_teams and old.get("kickoff_utc") == new["kickoff_utc"]:
                total_unchanged += 1
                continue

            total_updates += 1
            label_old = f"{old.get('home_team')} vs {old.get('away_team')}"
            label_new = f"{new['home_team']} vs {new['away_team']}"
            change_desc = label_old if same_teams else f"{label_old} -> {label_new}"
            print(f"[{slot[0]} J{slot[1]}] id={old['id']}: {change_desc}"
                  + ("" if same_teams else "  (RESET score/status)"))

            if apply:
                update_doc = {"$set": fields_to_update}
                if unset_fields:
                    update_doc["$unset"] = unset_fields
                db.matches.update_one({"id": old["id"]}, update_doc)

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
