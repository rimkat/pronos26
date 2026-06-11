import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import DateNav from "@/components/DateNav";
import GroupSection from "@/components/GroupSection";
import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

export default function MatchesPage() {
  const { user } = useAuth();
  const [dates, setDates] = useState([]);
  const [selected, setSelected] = useState(null);
  const [groups, setGroups] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Charger toutes les dates au démarrage
  useEffect(() => {
    api.get("/matches/dates").then(({ data }) => {
      setDates(data);
      // Sélectionne aujourd'hui s'il est dans la liste, sinon la 1re date
      const today = new Date().toISOString().slice(0, 10);
      setSelected(data.includes(today) ? today : data[0]);
    });
  }, []);

  // Charger matchs de la date + prédictions utilisateur
  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    Promise.all([
      api.get("/matches/grouped", { params: { date: selected } }),
      user && user.id ? api.get("/predictions/me") : Promise.resolve({ data: [] }),
    ])
      .then(([g, p]) => {
        setGroups(g.data);
        setPredictions(p.data);
      })
      .finally(() => setLoading(false));
  }, [selected, user]);

  const predictionsMap = useMemo(() => {
    const map = {};
    predictions.forEach((p) => (map[p.match_id] = p));
    return map;
  }, [predictions]);

  return (
    <div className="max-w-4xl mx-auto px-3 sm:px-6 pb-16">
      {/* Hero compact */}
      <div className="relative mt-4 rounded-lg overflow-hidden border border-border">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1522778119026-d647f0596c20?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600)",
          }}
        />
        <div className="absolute inset-0 bg-black/70" />
        <div className="relative px-4 sm:px-6 py-5 sm:py-7">
          <div className="text-[10px] uppercase tracking-[0.2em] text-white/80 font-bold">
            Coupe du Monde · USA-Canada-Mexique
          </div>
          <h1 className="display text-white text-3xl sm:text-4xl font-black uppercase tracking-tight mt-1">
            Pronostics <span className="text-primary">2026</span>
          </h1>
          <p className="text-xs sm:text-sm text-white/70 mt-1 max-w-md">
            Saisis tes scores avant le coup d'envoi. Sauvegarde auto. 5 points max par match.
          </p>
          {!(user && user.id) && (
            <div className="mt-3 flex gap-2">
              <Link
                to="/register"
                data-testid="hero-register"
                className="inline-flex items-center text-xs font-bold uppercase tracking-wider bg-primary text-primary-foreground px-3 py-1.5 rounded-md hover:opacity-90"
              >
                Créer un compte
              </Link>
              <Link
                to="/login"
                data-testid="hero-login"
                className="inline-flex items-center text-xs font-bold uppercase tracking-wider bg-white/10 text-white border border-white/20 px-3 py-1.5 rounded-md hover:bg-white/20"
              >
                Se connecter
              </Link>
            </div>
          )}
        </div>
      </div>

      {dates.length > 0 && (
        <DateNav dates={dates} selected={selected} onSelect={setSelected} />
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" /> Chargement…
        </div>
      ) : groups.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground text-sm">
          Aucun match programmé pour cette date.
        </div>
      ) : (
        <div className="mt-2" data-testid="matches-list">
          {groups.map((g) => (
            <GroupSection
              key={
                g.phase === "knockout"
                  ? `KO-${g.round}`
                  : `${g.group}-${g.matchday}`
              }
              section={g}
              predictionsMap={predictionsMap}
            />
          ))}
        </div>
      )}

      {!loading && !(user && user.id) && groups.length > 0 && (
        <div className="mt-6 p-4 border border-dashed border-border rounded-md text-center text-xs sm:text-sm text-muted-foreground">
          Connecte-toi pour enregistrer tes pronostics et grimper au classement.
        </div>
      )}
    </div>
  );
}
