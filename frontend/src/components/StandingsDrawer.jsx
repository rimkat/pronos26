/**
 * Drawer (Sheet) affichant le classement en direct d'un groupe.
 */
import { useEffect, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetDescription,
} from "@/components/ui/sheet";
import { BarChart3 } from "lucide-react";
import api from "@/lib/api";

function flagUrl(code) {
  return `https://flagcdn.com/w40/${code}.png`;
}

export default function StandingsDrawer({ group }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    api
      .get(`/standings/${group}`)
      .then(({ data }) => setRows(data))
      .finally(() => setLoading(false));
  }, [open, group]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          data-testid={`standings-trigger-${group}`}
          className="flex items-center gap-1 text-[10px] sm:text-xs font-bold uppercase tracking-wider text-muted-foreground hover:text-primary transition-colors"
        >
          <BarChart3 className="h-3.5 w-3.5" />
          <span>Classement</span>
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-md" data-testid={`standings-sheet-${group}`}>
        <SheetHeader>
          <SheetTitle className="display text-2xl uppercase tracking-tight">
            Groupe {group}
          </SheetTitle>
          <SheetDescription>Classement en direct calculé à partir des matchs joués.</SheetDescription>
        </SheetHeader>

        <div className="mt-6">
          {loading ? (
            <div className="text-sm text-muted-foreground">Chargement…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
                  <th className="text-left py-2 font-bold">#</th>
                  <th className="text-left py-2 font-bold">Équipe</th>
                  <th className="text-center py-2 font-bold">J</th>
                  <th className="text-center py-2 font-bold">G</th>
                  <th className="text-center py-2 font-bold">N</th>
                  <th className="text-center py-2 font-bold">P</th>
                  <th className="text-center py-2 font-bold">Diff</th>
                  <th className="text-right py-2 font-bold">Pts</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={r.team} className="border-b border-border/40">
                    <td className="py-2 text-muted-foreground font-bold">{i + 1}</td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <img src={flagUrl(r.code)} alt="" className="w-5 h-3.5 rounded-sm ring-1 ring-border" />
                        <span className="font-bold">{r.team}</span>
                      </div>
                    </td>
                    <td className="py-2 text-center tabular-nums">{r.j}</td>
                    <td className="py-2 text-center tabular-nums">{r.g}</td>
                    <td className="py-2 text-center tabular-nums">{r.n}</td>
                    <td className="py-2 text-center tabular-nums">{r.p}</td>
                    <td className="py-2 text-center tabular-nums">
                      {r.diff > 0 ? `+${r.diff}` : r.diff}
                    </td>
                    <td className="py-2 text-right display font-black tabular-nums">{r.pts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
