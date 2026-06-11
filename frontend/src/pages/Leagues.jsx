/**
 * Page Ligues privées : créer, rejoindre, voir le classement de mes ligues.
 */
import { useEffect, useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Users, Copy, Link as LinkIcon, Crown, LogOut, Loader2 } from "lucide-react";

export default function LeaguesPage() {
  const { user, loading: authLoading } = useAuth();
  const [searchParams] = useSearchParams();
  const inviteFromUrl = searchParams.get("invite");

  const [leagues, setLeagues] = useState([]);
  const [selected, setSelected] = useState(null);
  const [members, setMembers] = useState([]);
  const [loadingLeagues, setLoadingLeagues] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [joinCode, setJoinCode] = useState(inviteFromUrl || "");
  const [createOpen, setCreateOpen] = useState(false);
  const [joinOpen, setJoinOpen] = useState(false);

  useEffect(() => {
    if (!user || !user.id) return;
    fetchMyLeagues();
  }, [user]);

  // Auto-rejoindre via lien ?invite=CODE
  useEffect(() => {
    if (inviteFromUrl && user && user.id) {
      setJoinOpen(true);
    }
  }, [inviteFromUrl, user]);

  const fetchMyLeagues = async () => {
    setLoadingLeagues(true);
    try {
      const { data } = await api.get("/leagues/me");
      setLeagues(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
        loadMembers(data[0].id);
      }
    } finally {
      setLoadingLeagues(false);
    }
  };

  const loadMembers = async (id) => {
    const { data } = await api.get(`/leagues/${id}/leaderboard`);
    setMembers(data);
  };

  const selectLeague = (lg) => {
    setSelected(lg);
    loadMembers(lg.id);
  };

  const createLeague = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const { data } = await api.post("/leagues", { name: newName });
      toast.success(`Ligue "${data.name}" créée !`);
      setNewName("");
      setCreateOpen(false);
      await fetchMyLeagues();
      setSelected(data);
      loadMembers(data.id);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setCreating(false);
    }
  };

  const joinLeague = async () => {
    if (!joinCode.trim()) return;
    try {
      const { data } = await api.post("/leagues/join", {
        invite_code: joinCode.trim().toUpperCase(),
      });
      toast.success(`Tu as rejoint "${data.name}" !`);
      setJoinCode("");
      setJoinOpen(false);
      await fetchMyLeagues();
      setSelected(data);
      loadMembers(data.id);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const copyInvite = (lg) => {
    const url = `${window.location.origin}/ligues?invite=${lg.invite_code}`;
    navigator.clipboard.writeText(url);
    toast.success("Lien d'invitation copié !");
  };

  const copyCode = (lg) => {
    navigator.clipboard.writeText(lg.invite_code);
    toast.success(`Code "${lg.invite_code}" copié !`);
  };

  const leaveLeague = async (lg) => {
    if (!confirm(`Quitter la ligue "${lg.name}" ?`)) return;
    try {
      await api.delete(`/leagues/${lg.id}/leave`);
      toast.success("Ligue quittée");
      setSelected(null);
      setMembers([]);
      await fetchMyLeagues();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  if (authLoading) return null;
  if (!user || !user.id) return <Navigate to="/login" replace />;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8" data-testid="leagues-page">
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
            Entre potes
          </div>
          <h1 className="display text-3xl sm:text-4xl font-black uppercase tracking-tight">
            Mes ligues privées
          </h1>
        </div>
        <div className="flex gap-2">
          <Dialog open={joinOpen} onOpenChange={setJoinOpen}>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                data-testid="join-league-btn"
                className="font-bold uppercase tracking-wide text-xs"
              >
                <LinkIcon className="h-3.5 w-3.5 mr-1.5" /> Rejoindre
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="display uppercase tracking-tight">
                  Rejoindre une ligue
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-2 mt-3">
                <Label htmlFor="join-code" className="text-xs uppercase font-bold">
                  Code d'invitation
                </Label>
                <Input
                  id="join-code"
                  data-testid="join-league-code-input"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="ABCDEF"
                  className="h-11 tracking-widest text-lg uppercase"
                  maxLength={10}
                />
              </div>
              <DialogFooter>
                <Button onClick={joinLeague} data-testid="join-league-submit" className="font-bold uppercase">
                  Rejoindre
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button
                size="sm"
                data-testid="create-league-btn"
                className="font-bold uppercase tracking-wide text-xs"
              >
                <Plus className="h-3.5 w-3.5 mr-1.5" /> Créer
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="display uppercase tracking-tight">
                  Créer une ligue privée
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-2 mt-3">
                <Label htmlFor="lg-name" className="text-xs uppercase font-bold">
                  Nom de la ligue
                </Label>
                <Input
                  id="lg-name"
                  data-testid="create-league-name-input"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Les potes du bureau"
                  className="h-11"
                  maxLength={40}
                />
              </div>
              <DialogFooter>
                <Button
                  onClick={createLeague}
                  disabled={creating}
                  data-testid="create-league-submit"
                  className="font-bold uppercase"
                >
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Créer"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loadingLeagues ? (
        <div className="py-16 flex justify-center text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" /> Chargement…
        </div>
      ) : leagues.length === 0 ? (
        <div className="mt-8 border border-dashed border-border rounded-md p-10 text-center">
          <Users className="h-10 w-10 mx-auto text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            Aucune ligue pour le moment. Crée la tienne ou rejoins celle d'un pote.
          </p>
        </div>
      ) : (
        <div className="mt-6 grid md:grid-cols-[260px_1fr] gap-6">
          {/* Liste de mes ligues */}
          <aside className="space-y-2">
            {leagues.map((lg) => (
              <button
                key={lg.id}
                data-testid={`league-card-${lg.id}`}
                onClick={() => selectLeague(lg)}
                className={`w-full text-left p-3 rounded-md border transition-all ${
                  selected?.id === lg.id
                    ? "border-primary bg-primary/10"
                    : "border-border bg-card hover:bg-secondary"
                }`}
              >
                <div className="display font-bold uppercase tracking-tight text-sm">
                  {lg.name}
                </div>
                <div className="flex items-center justify-between mt-1 text-xs text-muted-foreground">
                  <span>{lg.member_count} membre{lg.member_count > 1 ? "s" : ""}</span>
                  {lg.owner_id === user.id && (
                    <span className="inline-flex items-center gap-1 text-primary font-bold uppercase tracking-wider text-[10px]">
                      <Crown className="h-3 w-3" /> Owner
                    </span>
                  )}
                </div>
              </button>
            ))}
          </aside>

          {/* Détail ligue */}
          <main>
            {selected ? (
              <div className="bg-card border border-border rounded-md p-5">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div>
                    <h2 className="display text-2xl font-black uppercase tracking-tight">
                      {selected.name}
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">
                      Créée par <span className="font-bold">{selected.owner_pseudo}</span> ·{" "}
                      {selected.member_count} membre{selected.member_count > 1 ? "s" : ""}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => leaveLeague(selected)}
                    data-testid="leave-league-btn"
                    className="text-xs font-bold uppercase"
                  >
                    <LogOut className="h-3.5 w-3.5 mr-1.5" />
                    {selected.owner_id === user.id ? "Supprimer" : "Quitter"}
                  </Button>
                </div>

                {/* Bloc invite */}
                <div className="mt-4 p-3 rounded-md bg-secondary/40 border border-border">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
                    Invite tes potes
                  </div>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <code
                      data-testid="league-invite-code"
                      className="display text-2xl font-black tracking-widest bg-background border border-border px-3 py-1.5 rounded-md"
                    >
                      {selected.invite_code}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyCode(selected)}
                      data-testid="copy-code-btn"
                      className="font-bold uppercase text-xs"
                    >
                      <Copy className="h-3.5 w-3.5 mr-1" /> Code
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => copyInvite(selected)}
                      data-testid="copy-link-btn"
                      className="font-bold uppercase text-xs"
                    >
                      <LinkIcon className="h-3.5 w-3.5 mr-1" /> Copier le lien
                    </Button>
                  </div>
                </div>

                {/* Classement de la ligue */}
                <div className="mt-5">
                  <h3 className="display text-sm font-bold uppercase tracking-widest text-muted-foreground mb-2">
                    Classement
                  </h3>
                  <div className="divide-y divide-border/40 border border-border rounded-md overflow-hidden">
                    {members.map((m) => {
                      const isMe = m.user_id === user.id;
                      return (
                        <div
                          key={m.user_id}
                          data-testid={`league-member-${m.user_id}`}
                          className={`flex items-center justify-between px-4 py-3 ${
                            isMe ? "bg-primary/10" : ""
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="display text-lg font-black w-7 tabular-nums text-muted-foreground">
                              {m.rank}
                            </span>
                            <span className={`font-bold ${isMe ? "text-primary" : ""}`}>
                              {m.pseudo}
                              {isMe && (
                                <span className="ml-2 text-[10px] uppercase tracking-wider text-primary font-bold">
                                  toi
                                </span>
                              )}
                            </span>
                          </div>
                          <div className="display text-xl font-black tabular-nums">
                            {m.total_points}
                            <span className="text-xs text-muted-foreground font-bold ml-1">pts</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="border border-dashed border-border rounded-md p-10 text-center text-sm text-muted-foreground">
                Sélectionne une ligue à gauche.
              </div>
            )}
          </main>
        </div>
      )}
    </div>
  );
}
