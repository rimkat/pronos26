import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Navigate, Link } from "react-router-dom";
import { Trophy, Target, TrendingUp, Users, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState(null);
  const [recent, setRecent] = useState([]);
  const [predictionsRaw, setPredictionsRaw] = useState([]);
  const [matchesById, setMatchesById] = useState({});

  useEffect(() => {
    if (!user || !user.id) return;
    api.get("/dashboard").then(({ data }) => setData(data));
    api.get("/predictions/me").then(({ data }) => setPredictionsRaw(data));
    api.get("/matches").then(({ data }) => {
      const map = {};
      data.forEach((m) => (map[m.id] = m));
      setMatchesById(map);
    });
  }, [user]);

  // Trie les pronostics par date de match (kickoff_utc) une fois que les
  // deux jeux de données (predictions + matches) sont disponibles.
  useEffect(() => {
    if (predictionsRaw.length === 0) {
      setRecent([]);
      return;
    }
    const sorted = [...predictionsRaw].sort((a, b) => {
      const matchA = matchesById[a.match_id];
      const matchB = matchesById[b.match_id];
      const dateA = matchA?.kickoff_utc ? new Date(matchA.kickoff_utc).getTime() : 0;
      const dateB = matchB?.kickoff_utc ? new Date(matchB.kickoff_utc).getTime() : 0;
      return dateA - dateB; // du plus ancien au plus récent
    });
    setRecent(sorted);
  }, [predictionsRaw, matchesById]);

  if (authLoading) return null;
  if (!user || !user.id) return <Navigate to="/login" replace />;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8" data-testid="dashboard-page">
      {/* Hero header */}
      <div className="relative rounded-lg overflow-hidden border border-border">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1522778119026-d647f0596c20?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600)",
          }}
        />
        <div className="absolute inset-0 bg-black/75" />
        <div className="relative p-6 sm:p-8 text-white">
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/70 font-bold">
            Tableau de bord
          </div>
          <h1 className="display text-3xl sm:text-4xl font-black uppercase tracking-tight mt-1">
            Salam <span className="text-primary">{user.pseudo}</span>
          </h1>

          {user.pseudo === "K" && (
  <Link to="/admin">
    <Shield className="h-5 w-5 text-primary" />
  </Link>
)}
        </div>
      </div>

      {!data ? (
        <div className="py-16 flex justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" /> Chargement…
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6">
            <StatCard
              icon={Trophy}
              label="Points totaux"
              value={data.total_points}
              accent
              testid="stat-points"
            />
            <StatCard
              icon={TrendingUp}
              label="Rang général"
              value={data.rank ? `#${data.rank}` : "—"}
              testid="stat-rank"
            />
            <StatCard
              icon={Users}
              label="Joueurs"
              value={data.total_users}
              testid="stat-users"
            />
            <StatCard
              icon={Target}
              label="Pronos saisis"
              value={data.predictions_count}
              testid="stat-predictions"
            />
          </div>

          <div className="mt-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="display text-xl font-bold uppercase tracking-wide">
                Tes derniers pronostics
              </h2>
              <Link
                to="/"
                data-testid="goto-matches"
                className="text-xs font-bold uppercase tracking-wider text-primary hover:underline"
              >
                Tous les matchs →
              </Link>
            </div>

            {recent.length === 0 ? (
              <div className="border border-dashed border-border rounded-md p-8 text-center text-sm text-muted-foreground">
                Aucun pronostic encore.{" "}
                <Link to="/" className="text-primary font-bold underline">
                  Commencer
                </Link>
              </div>
            ) : (
              <div className="border border-border rounded-md overflow-hidden divide-y divide-border/40 bg-card">
                {recent.map((p) => {
                  const match = matchesById[p.match_id];
                  const isFinished = match?.status === "finished";
                  const isLive = match?.status === "live";
                  return (
                  <div
                    key={p.id}
                    className={`flex items-center justify-between px-4 py-3 text-sm gap-2 ${
                      isFinished
                        ? "bg-muted/40 text-muted-foreground"
                        : isLive
                        ? "bg-primary/10 ring-1 ring-inset ring-primary/40"
                        : ""
                    }`}
                    data-testid={`recent-pred-${p.id}`}
                  >
                    <div className="flex flex-col items-center text-center">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Ton prono
                      </span>
                      <span className="font-bold tabular-nums">
                        {p.home_score_predicted} - {p.away_score_predicted}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground px-2 text-center flex-1 flex flex-col items-center leading-tight">
                      {match ? (
                        <>
                          <span className="truncate max-w-full">{match.home_team}</span>
                          <span className="text-[10px] text-muted-foreground/60">vs</span>
                          <span className="truncate max-w-full">{match.away_team}</span>
                        </>
                      ) : (
                        `Match #${p.match_id.slice(0, 8)}`
                      )}
                    </div>
                    {isFinished ? (
                      <div className="flex flex-col items-center text-center">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          Résultat
                        </span>
                        <span className="font-bold tabular-nums">
                          {match.home_score_actual} - {match.away_score_actual}
                        </span>
                      </div>
                    ) : (
                      <div className={`text-[10px] uppercase tracking-wider px-2 ${isLive ? "text-primary font-bold animate-pulse" : "text-muted-foreground"}`}>
                        {isLive ? "En cours" : "À venir"}
                      </div>
                    )}
                    <div
                      className={`display font-black text-base text-right min-w-[3.5rem] ${
                        p.points_earned > 0 ? "text-primary" : "text-muted-foreground"
                      }`}
                    >
                      {isFinished ? (
                        <>
                          {p.points_earned} pt{p.points_earned > 1 ? "s" : ""}
                        </>
                      ) : (
                        "—"
                      )}
                    </div>
                  </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-10 p-5 border border-border rounded-md bg-card">
            <h3 className="display text-sm font-bold uppercase tracking-widest text-muted-foreground">
              Barème
            </h3>
            <ul className="mt-2 space-y-1 text-sm">
              <li>
                <span className="display font-black text-primary mr-2">+1</span>
                Bon résultat (1N2)
              </li>
              <li>
                <span className="display font-black text-primary mr-2">+1</span>
                Bonne différence de buts
              </li>
              <li>
                <span className="display font-black text-primary mr-2">+3</span>
                Score exact (bonus)
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent, testid }) {
  return (
    <div
      data-testid={testid}
      className={`p-4 rounded-md border ${
        accent ? "border-primary/30 bg-primary/5" : "border-border bg-card"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">
          {label}
        </span>
        <Icon className={`h-4 w-4 ${accent ? "text-primary" : "text-muted-foreground"}`} />
      </div>
      <div
        className={`display text-3xl sm:text-4xl font-black mt-1 tabular-nums ${
          accent ? "text-primary" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}
