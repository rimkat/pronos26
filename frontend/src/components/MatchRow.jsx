/**
 * Ligne de match style L'Équipe : drapeaux + noms alignés, heure & chaînes au centre, inputs scores à droite.
 */
import { useEffect, useRef, useState } from "react";
import { Check, ChevronUp, Loader2, Lock, Users } from "lucide-react";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

function flagUrl(code) {
  return `https://flagcdn.com/w80/${code}.png`;
}

function formatHour(h) {
  return `${String(h).padStart(2, "0")}h${"00"}`;
}

export default function MatchRow({ match, prediction }) {
  const { user } = useAuth();
  const isAuth = user && user.id;
  const isTBD = !match.home_code || !match.away_code;
  const hasKickedOff = new Date(match.kickoff_utc).getTime() <= Date.now();
  const isLocked = match.status !== "scheduled" || isTBD || hasKickedOff;

  const [home, setHome] = useState(prediction?.home_score_predicted ?? "");
  const [away, setAway] = useState(prediction?.away_score_predicted ?? "");
  const [state, setState] = useState("idle"); // idle | saving | saved | error
  const [errMsg, setErrMsg] = useState("");
  const timer = useRef(null);

  // Panneau pronos des autres participants
  const [showPronos, setShowPronos] = useState(false);
  const [pronos, setPronos] = useState(null);
  const [pronosLoading, setPronosLoading] = useState(false);

  // Sync depuis prop si l'utilisateur se reconnecte ou change de date
  useEffect(() => {
    setHome(prediction?.home_score_predicted ?? "");
    setAway(prediction?.away_score_predicted ?? "");
  }, [prediction?.id]);

  // Sauvegarde debounce 700ms
  useEffect(() => {
    if (!isAuth || isLocked) return;
    if (home === "" || away === "") return;
    if (
      prediction &&
      Number(home) === prediction.home_score_predicted &&
      Number(away) === prediction.away_score_predicted
    ) {
      return;
    }
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setState("saving");
      try {
        await api.post("/predictions", {
          match_id: match.id,
          home_score_predicted: Number(home),
          away_score_predicted: Number(away),
        });
        setState("saved");
        setTimeout(() => setState("idle"), 1500);
      } catch (e) {
        setErrMsg(formatApiError(e.response?.data?.detail) || "Erreur");
        setState("error");
        setTimeout(() => setState("idle"), 2000);
      }
    }, 700);
    return () => timer.current && clearTimeout(timer.current);
  }, [home, away, isAuth, isLocked, match.id, prediction]);

  const handleNum = (setter) => (e) => {
    const v = e.target.value.replace(/[^0-9]/g, "").slice(0, 2);
    setter(v);
  };

  const togglePronos = async () => {
    if (!isAuth) return;
    if (showPronos) {
      setShowPronos(false);
      return;
    }
    setShowPronos(true);
    if (pronos !== null) return; // déjà chargé
    setPronosLoading(true);
    try {
      const res = await api.get(`/predictions/match/${match.id}`);
      setPronos(res.data);
    } catch {
      setPronos([]);
    } finally {
      setPronosLoading(false);
    }
  };

  const Indicator = () => {
    if (!isAuth) return null;
    if (state === "saving") return <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />;
    if (state === "saved") return <Check className="h-3.5 w-3.5 text-green-500" />;
    if (state === "error")
      return (
        <span className="text-[10px] text-destructive font-bold uppercase" title={errMsg}>
          err
        </span>
      );
    return <span className="w-3.5 h-3.5" />;
  };

  const isFinished = match.status === "finished";
  const isLive = match.status === "live";
  const canSeePronos = isAuth && isLocked && !isTBD;

  return (
    <div data-testid={`match-row-${match.id}`}>
      <div
        className={`flex items-center gap-2 sm:gap-3 py-3 px-3 border-b border-border/40 transition-colors ${
          isFinished
            ? "bg-muted/40 text-muted-foreground"
            : isLive
            ? "bg-primary/10 ring-1 ring-inset ring-primary/40"
            : "hover:bg-secondary/40"
        }`}
      >
        {/* Heure + chaînes */}
        <div className="flex flex-col items-center min-w-[58px] sm:min-w-[72px]">
          {isLive ? (
            <span className="text-[10px] sm:text-xs font-black uppercase tracking-wider text-primary animate-pulse">
              ● Live
            </span>
          ) : (
            <span className="display text-base sm:text-lg font-bold leading-none">
              {formatHour(match.kickoff_hour_paris)}
            </span>
          )}
          <span className="text-[9px] sm:text-[10px] text-muted-foreground mt-1 text-center leading-tight max-w-[70px] truncate">
            {match.broadcast_channels}
          </span>
        </div>

        {/* Équipes */}
        <div className="flex-1 min-w-0 flex flex-col gap-1">
          <TeamLine name={match.home_team} code={match.home_code} score={match.home_score_actual} />
          <TeamLine name={match.away_team} code={match.away_code} score={match.away_score_actual} />
        </div>

        {/* Pronostic */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1">
            <input
              type="number"
              value={home}
              onChange={handleNum(setHome)}
              disabled={!isAuth || isLocked}
              placeholder="-"
              data-testid={`score-input-home-${match.id}`}
              className="score-input w-9 h-10 sm:w-11 sm:h-11 text-center text-lg sm:text-xl font-black bg-card border border-input rounded-md focus:ring-2 focus:ring-primary focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <span className="text-muted-foreground font-bold text-sm">-</span>
            <input
              type="number"
              value={away}
              onChange={handleNum(setAway)}
              disabled={!isAuth || isLocked}
              placeholder="-"
              data-testid={`score-input-away-${match.id}`}
              className="score-input w-9 h-10 sm:w-11 sm:h-11 text-center text-lg sm:text-xl font-black bg-card border border-input rounded-md focus:ring-2 focus:ring-primary focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <div className="flex flex-col items-center gap-0.5 w-6">
            {isLocked ? <Lock className="h-3.5 w-3.5 text-muted-foreground" /> : <Indicator />}
            {canSeePronos && (
              <button
                onClick={togglePronos}
                title={showPronos ? "Masquer les pronostics" : "Voir les pronostics"}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPronos ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <Users className="h-3.5 w-3.5" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Panneau pronos des participants */}
      {showPronos && (
        <div className="border-b border-border/40 bg-muted/20 px-3 py-2">
          {pronosLoading ? (
            <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Chargement…
            </div>
          ) : pronos && pronos.length === 0 ? (
            <p className="text-xs text-muted-foreground py-1">Aucun pronostic enregistré.</p>
          ) : (
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {pronos?.map((p) => (
                <PronoChip
                  key={p.user_id}
                  pseudo={p.pseudo}
                  home={p.home_score_predicted}
                  away={p.away_score_predicted}
                  points={p.points_earned}
                  isMe={p.user_id === user?.id}
                  isFinished={isFinished}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PronoChip({ pseudo, home, away, points, isMe, isFinished }) {
  return (
    <div className={`flex items-center gap-1.5 text-xs py-0.5 ${isMe ? "font-bold text-primary" : "text-muted-foreground"}`}>
      <span className="truncate max-w-[80px]">{pseudo}{isMe ? " (moi)" : ""}</span>
      <span className="tabular-nums font-black">{home}-{away}</span>
      {isFinished && points > 0 && (
        <span className="text-[10px] text-green-600 font-bold">+{points}pts</span>
      )}
    </div>
  );
}

function TeamLine({ name, code, score }) {
  return (
    <div className="flex items-center gap-2">
      {code ? (
        <img
          src={flagUrl(code)}
          alt={name}
          className="w-6 h-4 sm:w-7 sm:h-5 object-cover rounded-[2px] ring-1 ring-border"
          loading="lazy"
        />
      ) : (
        <div className="w-6 h-4 sm:w-7 sm:h-5 rounded-[2px] ring-1 ring-dashed ring-border bg-muted/30" />
      )}
      <span className={`font-bold text-sm sm:text-[15px] truncate ${!code ? "text-muted-foreground italic" : ""}`}>
        {name}
      </span>
      {score !== null && score !== undefined && (
        <span className="ml-auto display text-base font-black tabular-nums">{score}</span>
      )}
    </div>
  );
}
