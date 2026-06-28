/**
 * Section : phase de groupes OU phase à élimination directe.
 */
import MatchRow from "./MatchRow";
import StandingsDrawer from "./StandingsDrawer";

const ORDINALS = {
  1: "1re journée",
  2: "2e journée",
  3: "3e journée",
};

const KO_ICONS = {
  R32: "🏟️",
  R16: "🔥",
  QF: "⚡",
  SF: "🏆",
  "3RD": "🥉",
  F: "👑",
};

export default function GroupSection({ section, predictionsMap }) {
  const isKO = section.phase === "knockout";

  return (
    <section
      data-testid={
        isKO
          ? `ko-section-${section.round}`
          : `group-section-${section.group}-${section.matchday}`
      }
      className="mt-5 first:mt-0"
    >
      <div
        className={`flex items-center justify-between px-3 py-2 border rounded-md ${
          isKO
            ? "bg-primary/10 border-primary/30"
            : "bg-card border-border"
        }`}
      >
        <h3 className="display text-sm sm:text-base font-bold uppercase tracking-widest">
          {isKO ? (
            <>
              <span className="text-primary mr-2">
                {KO_ICONS[section.round] || "•"}
              </span>
              {section.round_label}
            </>
          ) : (
            <>
              Groupe {section.group}
              <span className="text-muted-foreground font-bold ml-2">
                · {ORDINALS[section.matchday] || `${section.matchday}e journée`}
              </span>
            </>
          )}
        </h3>
        {!isKO && <StandingsDrawer group={section.group} />}
      </div>

      <div className="bg-card border-x border-b border-border rounded-b-md overflow-hidden">
        {section.matches.map((m) => (
          <MatchRow key={m.id} match={m} prediction={predictionsMap[m.id]} />
        ))}
      </div>
    </section>
  );
}
