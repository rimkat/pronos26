/**
 * Section d'un groupe (titre + bouton classement + liste des matchs).
 */
import MatchRow from "./MatchRow";
import StandingsDrawer from "./StandingsDrawer";

const ORDINALS = {
  1: "1re journée",
  2: "2e journée",
  3: "3e journée",
};

export default function GroupSection({ group, matchday, matches, predictionsMap }) {
  return (
    <section
      data-testid={`group-section-${group}-${matchday}`}
      className="mt-5 first:mt-0"
    >
      <div className="flex items-center justify-between px-3 py-2 bg-card border border-border rounded-md">
        <h3 className="display text-sm sm:text-base font-bold uppercase tracking-widest">
          Groupe {group}
          <span className="text-muted-foreground font-bold ml-2">
            · {ORDINALS[matchday] || `${matchday}e journée`}
          </span>
        </h3>
        <StandingsDrawer group={group} />
      </div>

      <div className="bg-card border-x border-b border-border rounded-b-md overflow-hidden">
        {matches.map((m) => (
          <MatchRow key={m.id} match={m} prediction={predictionsMap[m.id]} />
        ))}
      </div>
    </section>
  );
}
