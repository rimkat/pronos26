import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Trophy, Crown, Medal } from "lucide-react";

const ICONS = { 1: Crown, 2: Medal, 3: Medal };
const COLORS = { 1: "text-yellow-400", 2: "text-zinc-300", 3: "text-amber-600" };

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.get("/leaderboard").then(({ data }) => setRows(data));
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" data-testid="leaderboard-page">
      <div className="flex items-center gap-2 mb-1">
        <Trophy className="h-4 w-4 text-primary" />
        <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
          Top pronostiqueurs
        </span>
      </div>
      <h1 className="display text-3xl sm:text-4xl font-black uppercase tracking-tight">
        Classement général
      </h1>

      <div className="mt-6 border border-border rounded-md overflow-hidden bg-card">
        {rows.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            Personne n'a encore marqué de points. Soyez le premier !
          </div>
        ) : (
          rows.map((r) => {
            const Icon = ICONS[r.rank];
            const isMe = user && user.pseudo === r.pseudo;
            return (
              <div
                key={r.rank}
                data-testid={`leaderboard-row-${r.rank}`}
                className={`flex items-center justify-between px-4 py-3 border-b border-border/40 last:border-b-0 ${
                  isMe ? "bg-primary/10" : ""
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="display text-xl font-black w-8 tabular-nums text-muted-foreground">
                    {r.rank}
                  </span>
                  {Icon && <Icon className={`h-4 w-4 ${COLORS[r.rank]}`} />}
                  <span className={`font-bold ${isMe ? "text-primary" : ""}`}>
                    {r.pseudo}
                    {isMe && (
                      <span className="ml-2 text-[10px] uppercase tracking-wider text-primary font-bold">
                        toi
                      </span>
                    )}
                  </span>
                </div>
                <div className="display text-2xl font-black tabular-nums">
                  {r.total_points}
                  <span className="text-xs text-muted-foreground font-bold ml-1">pts</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
