import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Navigate } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  Shield, Loader2, ChevronDown, ChevronUp,
  CheckCircle2, AlertCircle, Trophy, Users, Flag
} from "lucide-react";
import { Button } from "@/components/ui/button";

const ADMIN_TOKEN = "wc062026-admin-secret-token";

const adminApi = (method, path, body) =>
  api({ method, url: path, data: body, headers: { "x-admin-token": ADMIN_TOKEN } });

// ── Helpers ──────────────────────────────────────────────────────
const FLAG = (code) => code ? `https://flagcdn.com/w40/${code}.png` : null;

function statusColor(status) {
  if (status === "finished") return "text-muted-foreground";
  if (status === "live") return "text-green-500";
  return "text-foreground";
}

function statusLabel(status) {
  if (status === "finished") return "Terminé";
  if (status === "live") return "En cours";
  return "À venir";
}

// ── Section : Correction de score ────────────────────────────────
function MatchScoreEditor({ match, onSaved }) {
  const [open, setOpen] = useState(false);
  const [homeScore, setHomeScore] = useState(match.home_score_actual ?? "");
  const [awayScore, setAwayScore] = useState(match.away_score_actual ?? "");
  const [status, setStatus] = useState(match.status);
  const [winner, setWinner] = useState("");
  const [saving, setSaving] = useState(false);

  const isKnockout = match.phase === "knockout";
  const scoresDraw = homeScore !== "" && awayScore !== "" && Number(homeScore) === Number(awayScore);
  const needsWinner = isKnockout && scoresDraw && status === "finished";

  const handleSave = async () => {
    if (homeScore === "" || awayScore === "") return toast.error("Remplis les deux scores");
    if (needsWinner && !winner) return toast.error("Indique le vainqueur (tirs au but)");
    setSaving(true);
    try {
      await adminApi("POST", "/admin/match-result", {
        match_id: match.id,
        home_score_actual: Number(homeScore),
        away_score_actual: Number(awayScore),
        status,
        ...(winner ? { winner } : {}),
      });
      toast.success("Score mis à jour ✓");
      setOpen(false);
      onSaved?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-muted/40 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex items-center gap-1.5 shrink-0">
            {match.home_code && (
              <img src={FLAG(match.home_code)} alt="" className="w-5 h-3.5 object-cover rounded-sm" />
            )}
            <span className="font-bold text-sm truncate max-w-[80px]">{match.home_team}</span>
          </div>
          <span className="font-black text-sm tabular-nums text-primary">
            {match.home_score_actual ?? "–"} : {match.away_score_actual ?? "–"}
          </span>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="font-bold text-sm truncate max-w-[80px]">{match.away_team}</span>
            {match.away_code && (
              <img src={FLAG(match.away_code)} alt="" className="w-5 h-3.5 object-cover rounded-sm" />
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`text-[10px] uppercase tracking-wide font-bold ${statusColor(match.status)}`}>
            {statusLabel(match.status)}
          </span>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-3 bg-muted/20 border-t border-border space-y-4">
          {/* Scores */}
          <div className="grid grid-cols-3 gap-2 items-center">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] uppercase tracking-wide text-muted-foreground font-bold">
                {match.home_team}
              </label>
              <input
                type="number" min="0" max="99"
                value={homeScore}
                onChange={(e) => setHomeScore(e.target.value)}
                className="border border-border rounded-md px-3 py-2 text-center font-black text-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="text-center font-black text-muted-foreground text-lg mt-5">:</div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] uppercase tracking-wide text-muted-foreground font-bold text-right">
                {match.away_team}
              </label>
              <input
                type="number" min="0" max="99"
                value={awayScore}
                onChange={(e) => setAwayScore(e.target.value)}
                className="border border-border rounded-md px-3 py-2 text-center font-black text-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Statut */}
          <div className="flex gap-2">
            {["live", "finished"].map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={`flex-1 py-2 rounded-md text-xs font-bold uppercase tracking-wide border transition-all
                  ${status === s
                    ? s === "live"
                      ? "border-green-500 bg-green-500/10 text-green-600"
                      : "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/40"
                  }`}
              >
                {s === "live" ? "⏱ En cours" : "✅ Terminé"}
              </button>
            ))}
          </div>

          {/* Vainqueur TAB (knockout + nul + finished) */}
          {needsWinner && (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-wide font-bold text-muted-foreground">
                Vainqueur aux tirs au but
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { side: "home", name: match.home_team, code: match.home_code },
                  { side: "away", name: match.away_team, code: match.away_code },
                ].map(({ side, name, code }) => (
                  <button
                    key={side}
                    onClick={() => setWinner(side)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 font-bold text-sm transition-all
                      ${winner === side
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border hover:border-primary/50"
                      }`}
                  >
                    {code && <img src={FLAG(code)} alt="" className="w-6 h-4 object-cover rounded-sm" />}
                    {name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <Button
            className="w-full font-black uppercase tracking-widest"
            onClick={handleSave}
            disabled={saving}
          >
            {saving
              ? <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Enregistrement…</>
              : <><CheckCircle2 className="h-4 w-4 mr-2" /> Valider</>
            }
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Section : Équipes d'un match knockout ────────────────────────
function MatchTeamsEditor({ match, onSaved }) {
  const [open, setOpen] = useState(false);
  const [homeTeam, setHomeTeam] = useState(match.home_team || "");
  const [homeCode, setHomeCode] = useState(match.home_code || "");
  const [awayTeam, setAwayTeam] = useState(match.away_team || "");
  const [awayCode, setAwayCode] = useState(match.away_code || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await adminApi("PATCH", "/admin/match-teams", {
        match_id: match.id,
        home_team: homeTeam || undefined,
        home_code: homeCode || undefined,
        away_team: awayTeam || undefined,
        away_code: awayCode || undefined,
      });
      toast.success("Équipes mises à jour ✓");
      setOpen(false);
      onSaved?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-muted/40 transition-colors"
      >
        <div className="text-sm font-bold text-left">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground block">
            {match.round_label} #{match.matchday}
          </span>
          {match.home_team} vs {match.away_team}
        </div>
        {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-3 bg-muted/20 border-t border-border space-y-3">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Équipe domicile", team: homeTeam, setTeam: setHomeTeam, code: homeCode, setCode: setHomeCode },
              { label: "Équipe extérieur", team: awayTeam, setTeam: setAwayTeam, code: awayCode, setCode: setAwayCode },
            ].map(({ label, team, setTeam, code, setCode }) => (
              <div key={label} className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-wide font-bold text-muted-foreground">{label}</label>
                <input
                  value={team}
                  onChange={(e) => setTeam(e.target.value)}
                  placeholder="Ex: France"
                  className="w-full border border-border rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toLowerCase())}
                  placeholder="Code (ex: fr)"
                  className="w-full border border-border rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary font-mono"
                />
              </div>
            ))}
          </div>
          <Button className="w-full font-black uppercase tracking-widest" onClick={handleSave} disabled={saving}>
            {saving ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Enregistrement…</> : <><Users className="h-4 w-4 mr-2" />Mettre à jour</>}
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Section : Résultat final spécial ────────────────────────────
function SpecialResultAdmin() {
  const [winner, setWinner] = useState("");
  const [runnerUp, setRunnerUp] = useState("");
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);

  const handleCompute = async () => {
    if (!winner.trim() || !runnerUp.trim()) return toast.error("Remplis les deux équipes");
    if (winner.trim() === runnerUp.trim()) return toast.error("Les deux équipes doivent être différentes");
    setSaving(true);
    try {
      const { data } = await adminApi("POST", "/admin/special-prediction-result", {
        winner: winner.trim(),
        runner_up: runnerUp.trim(),
      });
      setResult(data);
      toast.success(`Points calculés pour ${data.computed} joueurs ✓`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        À utiliser après la finale. Calcule et attribue les points des pronos spéciaux à tous les joueurs.
      </p>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wide font-bold text-muted-foreground">🥇 Vainqueur</label>
          <input
            value={winner}
            onChange={(e) => setWinner(e.target.value)}
            placeholder="Ex: France"
            className="w-full border border-border rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wide font-bold text-muted-foreground">🥈 Finaliste</label>
          <input
            value={runnerUp}
            onChange={(e) => setRunnerUp(e.target.value)}
            placeholder="Ex: Argentine"
            className="w-full border border-border rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>
      <Button
        className="w-full font-black uppercase tracking-widest"
        onClick={handleCompute}
        disabled={saving}
        variant="destructive"
      >
        {saving
          ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Calcul en cours…</>
          : <><Trophy className="h-4 w-4 mr-2" />Déclencher le calcul des points</>
        }
      </Button>
      {result && (
        <div className="flex items-center gap-2 text-sm text-green-600 font-bold bg-green-500/10 border border-green-500/30 rounded-md px-3 py-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {result.computed} joueurs mis à jour — {result.winner} bat {result.runner_up}
        </div>
      )}
    </div>
  );
}

// ── Page principale ──────────────────────────────────────────────
export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("scores");
  const [dateFilter, setDateFilter] = useState("all");
  const [dates, setDates] = useState([]);

  const fetchMatches = async () => {
    try {
      const { data } = await api.get("/matches");
      setMatches(data);
      const uniqueDates = [...new Set(data.map((m) => m.display_date))].sort();
      setDates(uniqueDates);
      // Filtre par défaut = aujourd'hui si disponible
      const today = new Date().toISOString().slice(0, 10);
      if (uniqueDates.includes(today)) setDateFilter(today);
    } catch {
      toast.error("Impossible de charger les matchs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMatches(); }, []);

  if (authLoading) return null;
  if (!user || !user.id) return <Navigate to="/login" replace />;
  if (user.pseudo !== "K.") return <Navigate to="/" replace />;

  const filteredMatches = dateFilter === "all"
    ? matches
    : matches.filter((m) => m.display_date === dateFilter);

  const knockoutMatches = matches.filter((m) => m.phase === "knockout");

  const TABS = [
    { id: "scores", label: "Scores", icon: Flag },
    { id: "teams", label: "Équipes", icon: Users },
    { id: "final", label: "Finale spéciale", icon: Trophy },
  ];

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10 border border-primary/30">
          <Shield className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="font-black uppercase tracking-tight text-lg">Panel Admin</h1>
          <p className="text-xs text-muted-foreground">Accès réservé · K</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-muted rounded-lg">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-bold uppercase tracking-wide transition-all
              ${activeTab === id ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* ── TAB SCORES ── */}
          {activeTab === "scores" && (
            <div className="space-y-4">
              {/* Filtre par date */}
              <div className="flex gap-2 overflow-x-auto pb-1">
                <button
                  onClick={() => setDateFilter("all")}
                  className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-bold border transition-all
                    ${dateFilter === "all" ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground"}`}
                >
                  Tous
                </button>
                {dates.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDateFilter(d)}
                    className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-bold border transition-all
                      ${dateFilter === d ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground"}`}
                  >
                    {new Date(d + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                {filteredMatches.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">Aucun match pour cette date</p>
                ) : (
                  filteredMatches.map((m) => (
                    <MatchScoreEditor key={m.id} match={m} onSaved={fetchMatches} />
                  ))
                )}
              </div>
            </div>
          )}

          {/* ── TAB ÉQUIPES ── */}
          {activeTab === "teams" && (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground mb-3">
                Modifie les équipes des matchs à élimination directe (utile si le bracket n'est pas rempli automatiquement).
              </p>
              {knockoutMatches.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">Aucun match knockout</p>
              ) : (
                knockoutMatches.map((m) => (
                  <MatchTeamsEditor key={m.id} match={m} onSaved={fetchMatches} />
                ))
              )}
            </div>
          )}

          {/* ── TAB FINALE SPÉCIALE ── */}
          {activeTab === "final" && (
            <div className="rounded-xl border border-border p-5 space-y-4">
              <div className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-primary" />
                <h2 className="font-black uppercase tracking-wide text-sm">Résultat final CdM</h2>
              </div>
              <SpecialResultAdmin />
            </div>
          )}
        </>
      )}
    </div>
  );
}
