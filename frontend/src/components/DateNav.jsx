/**
 * Barre de navigation par date - inspirée L'Équipe.
 * Affiche les dates au format court "mar. 9", "mer. 10" etc.
 */
import { useEffect, useRef } from "react";

const WEEKDAY = ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."];

function formatShort(dateStr) {
  const d = new Date(dateStr + "T12:00:00");
  return { wd: WEEKDAY[d.getDay()], day: d.getDate(), month: d.getMonth() + 1 };
}

export default function DateNav({ dates, selected, onSelect }) {
  const containerRef = useRef(null);
  const activeRef = useRef(null);

  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [selected]);

  return (
    <div
      ref={containerRef}
      className="flex overflow-x-auto whitespace-nowrap gap-1.5 py-3 no-scrollbar sticky top-14 z-40 bg-background/90 backdrop-blur-md border-b border-border"
      data-testid="date-nav"
    >
      {dates.map((dateStr) => {
        const { wd, day, month } = formatShort(dateStr);
        const active = dateStr === selected;
        return (
          <button
            key={dateStr}
            ref={active ? activeRef : null}
            onClick={() => onSelect(dateStr)}
            data-testid={`date-tab-${dateStr}`}
            className={`shrink-0 flex flex-col items-center justify-center w-14 sm:w-16 py-1.5 rounded-md border transition-all ${
              active
                ? "bg-primary text-primary-foreground border-primary shadow-sm"
                : "bg-card border-border text-foreground hover:bg-secondary"
            }`}
          >
            <span className={`text-[10px] uppercase font-medium tracking-wider ${active ? "opacity-90" : "text-muted-foreground"}`}>
              {wd}
            </span>
            <span className="display text-xl font-black leading-none">{day}</span>
            <span className={`text-[9px] uppercase tracking-wide ${active ? "opacity-80" : "text-muted-foreground"}`}>
              {month === 6 ? "juin" : month === 7 ? "juil." : ""}
            </span>
          </button>
        );
      })}
    </div>
  );
}
