import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Navigate } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import { Trophy, Medal, Star, Lock, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const FLAG = (code) => `https://flagcdn.com/w40/${code}.png`;

const TEAMS = [
  { name: "Afrique du Sud", code: "za" },
  { name: "Algérie",        code: "dz" },
  { name: "Allemagne",      code: "de" },
  { name: "Angleterre",     code: "gb-eng" },
  { name: "Argentine",      code: "ar" },
  { name: "Australie",      code: "au" },
  { name: "Autriche",       code: "at" },
  { name: "Belgique",       code: "be" },
  { name: "Bosnie-Herzégovine", code: "ba", short: "Bosnie-Herz." },
  { name: "Brésil",         code: "br" },
  { name: "Canada",         code: "ca" },
  { name: "Cap-Vert",       code: "cv" },
  { name: "Colombie",       code: "co" },
  { name: "Côte d'Ivoire",  code: "ci" },
  { name: "Croatie",        code: "hr" },
  { name: "Égypte",         code: "eg" },
  { name: "Équateur",       code: "ec" },
  { name: "Espagne",        code: "es" },
  { name: "États-Unis",     code: "us" },
  { name: "France",         code: "fr" },
  { name: "Ghana",          code: "gh" },
  { name: "Japon",          code: "jp" },
  { name: "Maroc",          code: "ma" },
  { name: "Mexique",        code: "mx" },
  { name: "Norvège",        code: "no" },
  { name: "Paraguay",       code: "py" },
  { name: "Pays-Bas",       code: "nl" },
  { name: "Portugal",       code: "pt" },
  { name: "RD Congo",       code: "cd" },
  { name: "Sénégal",        code: "sn" },
  { name: "Suède",          code: "se" },
  { name: "Suisse",         code: "ch" },
].sort((a, b) => a.name.localeCompare(b.name, "fr"));

// Countdown
function useCountdown(deadline) {
  const calc = () => {
    const diff = new Date(deadline) - new Date();
    if (diff <= 0) return null;
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    return { h, m, s };
  };
  const [remaining, setRemaining] = useState(calc);
  useEffect(() => {
    const t = setInterval(() => setRemaining(calc()), 1000);
    return () => clearInterval(t);
  }, [deadline]);
  return remaining;
}

// Carte style DateNav
function CountdownCard({ value, label }) {
  return (
    <div className="flex flex-col items-center justify-center w-16 sm:w-20 py-2.5 rounded-md border border-white/30 bg-white/15 backdrop-blur-sm">
      <span className="display text-3xl sm:text-4xl font-black leading-none text-white tabular-nums">
        {String(value).padStart(2, "0")}
      </span>
      <span className="text-[9px] uppercase tracking-wide text-white/70 mt-1">{label}</span>
    </div>
  );
}

function TeamButton({ team, selected, disabled, onClick }) {
  return (
    <button
      onClick={() => !disabled && onClick(team)}
      disabled={disabled && !selected}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-semibold transition-all
        ${selected
          ? "border-primary bg-primary/10 text-primary shadow-sm"
          : disabled
            ? "border-border text-muted-foreground opacity-40 cursor-not-allowed"
            : "border-border hover:border-primary/50 hover:bg-secondary text-foreground cursor-pointer"
        }`}
    >
      <img
        src={FLAG(team.code)}
        alt={team.name}
        className="w-6 h-4 shrink-0 object-cover rounded-sm"
        onError={(e) => { e.target.style.display = "none"; }}
      />
      <span className="truncate">{team.short ?? team.name}</span>
      {selected && <CheckCircle2 className="h-4 w-4 shrink-0 ml-auto text-primary" />}
    </button>
  );
}

export default function SpecialPredictionsPage() {
  const { user, loading: authLoading } = useAuth();
  const [existing, setExisting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Sélections en cours
  const [finalist1, setFinalist1] = useState(null); // premier finaliste
  const [finalist2, setFinalist2] = useState(null); // second finaliste
  const [winner, setWinner] = useState(null);        // lequel des 2 gagne

  const [allPreds, setAllPreds] = useState(null);

  const fetchPred = useCallback(async () => {
    try {
      const { data } = await api.get("/predictions/special/me");
      setExisting(data);
      if (data.winner) {
        // Trouver les objets équipe correspondants
        const w = TEAMS.find((t) => t.name === data.winner) || { name: data.winner, code: "" };
        const r = TEAMS.find((t) => t.name === data.runner_up) || { name: data.runner_up, code: "" };
        setFinalist1(w);
        setFinalist2(r);
        setWinner(w);
      }
    } catch {
      // pas de prono existant
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.id) fetchPred();
  }, [user, fetchPred]);

  // Charger tous les pronos si deadline passée
  useEffect(() => {
    if (existing?.closed) {
      api.get("/predictions/special/all")
        .then(({ data }) => setAllPreds(data))
        .catch(() => {});
    }
  }, [existing?.closed]);

  if (authLoading) return null;
  if (!user?.id) return <Navigate to="/login" replace />;

  const deadline = existing?.deadline || "2026-06-28T21:59:00Z";
  const closed = existing?.closed ?? new Date() > new Date(deadline);
  const countdown = useCountdown(deadline);

  // Gestion des sélections
  const handleTeamClick = (team) => {
    if (closed) return;
    if (!finalist1) { setFinalist1(team); return; }
    if (!finalist2 && team.name !== finalist1.name) { setFinalist2(team); return; }
    // Déselectionner
    if (finalist1?.name === team.name) {
      setFinalist1(finalist2);
      setFinalist2(null);
      if (winner?.name === team.name) setWinner(finalist2);
      return;
    }
    if (finalist2?.name === team.name) {
      setFinalist2(null);
      if (winner?.name === team.name) setWinner(null);
    }
  };

  const handleSubmit = async () => {
    if (!finalist1 || !finalist2 || !winner) return;
    const runner_up = winner.name === finalist1.name ? finalist2 : finalist1;
    setSaving(true);
    try {
      await api.post("/predictions/special", { winner: winner.name, runner_up: runner_up.name });
      toast.success("Prono enregistré !");
      fetchPred();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setSaving(false);
    }
  };

  const canSubmit = finalist1 && finalist2 && winner && !closed;
  const hasExisting = existing?.winner;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      {/* Hero */}
      <div className="relative rounded-xl overflow-hidden border border-border mb-8">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url(https://images.unsplash.com/photo-1508098682722-e99c43a406b2?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200)" }}
        />
        <div className="absolute inset-0 bg-red-950/80" />
        <div className="relative p-6 sm:p-8 text-white">
          <div className="text-[10px] uppercase tracking-[0.2em] text-red-200/70 font-bold mb-1">Prono Spécial</div>
          <h1 className="text-2xl sm:text-3xl font-black uppercase tracking-tight mb-1">
            🏆 La Finale
          </h1>
          <p className="text-red-100/80 text-sm mb-5">
            Qui seront les deux finalistes ? Qui soulèvera le trophée ?
          </p>

          {/* Countdown style cartes de dates */}
          {!closed && countdown ? (
            <div>
              <div className="text-[10px] uppercase tracking-widest text-red-200/60 font-bold mb-2">
                Clôture dans
              </div>
              <div className="flex items-center gap-1.5">
                <CountdownCard value={countdown.h} label="heure" />
                <span className="text-2xl font-black text-white/40 mb-0.5">:</span>
                <CountdownCard value={countdown.m} label="min" />
                <span className="text-2xl font-black text-white/40 mb-0.5">:</span>
                <CountdownCard value={countdown.s} label="sec" />
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-200/70 text-sm font-bold uppercase tracking-wide">
              <Lock className="h-4 w-4" /> Pronos clôturés
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : closed ? (
        /* ── Mode lecture après deadline ── */
        <div className="space-y-6">
          {/* Mon prono */}
          {hasExisting && (
            <div className="rounded-xl border border-border p-5">
              <h2 className="text-xs uppercase tracking-widest font-bold text-muted-foreground mb-4">Mon prono</h2>
              <MyPredictionDisplay pred={existing} pts={existing.points_earned} />
            </div>
          )}

          {/* Tous les pronos */}
          {allPreds && (
            <div className="rounded-xl border border-border p-5">
              <h2 className="text-xs uppercase tracking-widest font-bold text-muted-foreground mb-4">
                Tous les pronos ({allPreds.length})
              </h2>
              <div className="divide-y divide-border">
                {allPreds.map((p) => (
                  <div key={p.user_id} className="py-3 flex items-center justify-between gap-3">
                    <span className="font-bold text-sm text-foreground">{p.pseudo}</span>
                    <div className="flex items-center gap-3 text-sm">
                      <TeamPill name={p.winner} code={TEAMS.find(t=>t.name===p.winner)?.code} label="🥇" />
                      <TeamPill name={p.runner_up} code={TEAMS.find(t=>t.name===p.runner_up)?.code} label="🥈" />
                      {p.points_earned > 0 && (
                        <span className="font-black text-primary">+{p.points_earned} pts</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* ── Mode saisie ── */
        <div className="space-y-6">
          {/* Étape 1 : choisir les 2 finalistes */}
          <div className="rounded-xl border border-border p-5">
            <div className="flex items-center gap-2 mb-1">
              <Medal className="h-5 w-5 text-primary" />
              <h2 className="font-black uppercase tracking-wide text-sm">
                Étape 1 — Tes 2 finalistes
              </h2>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Sélectionne 2 équipes parmi les 32 qualifiés.{" "}
              {finalist1 && finalist2
                ? <span className="text-primary font-bold">✓ {finalist1.name} vs {finalist2.name}</span>
                : finalist1
                  ? <span className="text-amber-500 font-bold">Encore 1 à choisir…</span>
                  : "Clique sur 2 équipes."}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {TEAMS.map((team) => {
                const isSelected = finalist1?.name === team.name || finalist2?.name === team.name;
                const twoSelected = !!(finalist1 && finalist2);
                return (
                  <TeamButton
                    key={team.name}
                    team={team}
                    selected={isSelected}
                    disabled={twoSelected && !isSelected}
                    onClick={handleTeamClick}
                  />
                );
              })}
            </div>
          </div>

          {/* Étape 2 : choisir le vainqueur */}
          {finalist1 && finalist2 && (
            <div className="rounded-xl border border-primary/30 bg-primary/5 p-5">
              <div className="flex items-center gap-2 mb-1">
                <Trophy className="h-5 w-5 text-primary" />
                <h2 className="font-black uppercase tracking-wide text-sm">
                  Étape 2 — Qui gagne la Coupe ?
                </h2>
              </div>
              <p className="text-xs text-muted-foreground mb-4">Entre tes deux finalistes, lequel soulève le trophée ?</p>
              <div className="grid grid-cols-2 gap-3">
                {[finalist1, finalist2].map((team) => (
                  <button
                    key={team.name}
                    onClick={() => setWinner(team)}
                    className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all font-bold text-sm
                      ${winner?.name === team.name
                        ? "border-primary bg-primary text-primary-foreground shadow-lg scale-105"
                        : "border-border hover:border-primary/50 text-foreground"
                      }`}
                  >
                    <img
                      src={FLAG(team.code)}
                      alt={team.name}
                      className="w-12 h-8 object-cover rounded"
                    />
                    {team.name}
                    {winner?.name === team.name && <Trophy className="h-4 w-4" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bouton submit */}
          <div className="space-y-2">
            {hasExisting && (
              <p className="text-xs text-center text-muted-foreground">
                Prono actuel : <strong>{existing.winner}</strong> bat <strong>{existing.runner_up}</strong> — modifiable jusqu'à la clôture.
              </p>
            )}
            <Button
              className="w-full font-black uppercase tracking-widest"
              size="lg"
              onClick={handleSubmit}
              disabled={!canSubmit || saving}
            >
              {saving ? (
                <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Enregistrement…</>
              ) : hasExisting ? (
                <><Star className="h-4 w-4 mr-2" /> Modifier mon prono</>
              ) : (
                <><Star className="h-4 w-4 mr-2" /> Valider mon prono</>
              )}
            </Button>
          </div>

          {/* Récap barème */}
          <div className="rounded-xl border border-border p-4 bg-secondary/30">
            <h3 className="text-xs uppercase tracking-widest font-bold text-muted-foreground mb-3">Barème</h3>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between"><span>🏆 Bon vainqueur + bon finaliste</span><span className="font-black text-primary">28 pts</span></div>
              <div className="flex justify-between"><span>🥇 Bon vainqueur seulement</span><span className="font-bold">18 pts</span></div>
              <div className="flex justify-between"><span>🥈 Bon finaliste perdant seulement</span><span className="font-bold">15 pts</span></div>
              <div className="flex justify-between"><span>✅ Les 2 bonnes équipes (ordre inversé)</span><span className="font-bold">10 pts</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TeamPill({ name, code, label }) {
  return (
    <div className="flex items-center gap-1.5 text-xs font-semibold">
      <span>{label}</span>
      {code && (
        <img src={FLAG(code)} alt={name} className="w-5 h-3.5 object-cover rounded-sm" />
      )}
      <span>{name}</span>
    </div>
  );
}

function MyPredictionDisplay({ pred, pts }) {
  const winner = TEAMS.find((t) => t.name === pred.winner) || { name: pred.winner, code: "" };
  const runnerUp = TEAMS.find((t) => t.name === pred.runner_up) || { name: pred.runner_up, code: "" };
  return (
    <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
      <div className="flex flex-col items-center gap-2">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">🥇 Vainqueur</span>
        <img src={FLAG(winner.code)} alt={winner.name} className="w-16 h-11 object-cover rounded-lg shadow" />
        <span className="font-black text-foreground">{winner.name}</span>
      </div>
      <div className="text-2xl font-black text-muted-foreground">vs</div>
      <div className="flex flex-col items-center gap-2">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">🥈 Finaliste</span>
        <img src={FLAG(runnerUp.code)} alt={runnerUp.name} className="w-16 h-11 object-cover rounded-lg shadow" />
        <span className="font-black text-foreground">{runnerUp.name}</span>
      </div>
      {pts > 0 && (
        <div className="sm:ml-4 flex flex-col items-center">
          <span className="text-3xl font-black text-primary">+{pts}</span>
          <span className="text-xs text-muted-foreground font-bold uppercase">pts</span>
        </div>
      )}
    </div>
  );
}
