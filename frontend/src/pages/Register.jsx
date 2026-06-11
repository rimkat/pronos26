import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Trophy, Loader2, Lock } from "lucide-react";

export default function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [pseudo, setPseudo] = useState("");
  const [pin, setPin] = useState("");
  const [pinConfirm, setPinConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  if (user && user.id) return <Navigate to="/dashboard" replace />;

  const handle = async (e) => {
    e.preventDefault();
    if (pin !== pinConfirm) {
      toast.error("Les codes PIN ne correspondent pas");
      return;
    }
    setLoading(true);
    const res = await register(pseudo.trim(), pin);
    setLoading(false);
    if (res.ok) {
      toast.success("Compte créé. Que la meilleure prédiction gagne !");
      navigate("/dashboard");
    } else {
      toast.error(res.error);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] grid lg:grid-cols-2">
      <div className="relative hidden lg:block">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1665413811870-5b29a250f64a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-tl from-black/85 via-black/60 to-primary/40" />
        <div className="relative h-full flex flex-col justify-end p-10 text-white">
          <Trophy className="h-12 w-12 text-primary mb-3" />
          <h2 className="display text-5xl font-black uppercase leading-none tracking-tight">
            Rejoins<br /> l'arène.
          </h2>
          <p className="mt-3 text-white/70 max-w-sm">
            Crée ton compte en 30 secondes : un pseudo, un code PIN, et c'est parti.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12">
        <form
          onSubmit={handle}
          className="w-full max-w-sm space-y-5"
          data-testid="register-form"
        >
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
              Inscription
            </div>
            <h1 className="display text-3xl sm:text-4xl font-black uppercase tracking-tight mt-1">
              Crée ton compte
            </h1>
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <Lock className="h-3 w-3" /> Pas d'email, juste un pseudo et un code PIN. Note-les bien !
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pseudo" className="text-xs font-bold uppercase tracking-wide">
              Pseudo
            </Label>
            <Input
              id="pseudo" type="text" required minLength={2} maxLength={30}
              value={pseudo}
              onChange={(e) => setPseudo(e.target.value)}
              data-testid="register-pseudo-input"
              className="h-11"
              placeholder="Ton pseudo de captain"
              autoComplete="username"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pin" className="text-xs font-bold uppercase tracking-wide">
              Code PIN (4 à 6 chiffres)
            </Label>
            <Input
              id="pin" type="password" inputMode="numeric" pattern="\d{4,6}" required minLength={4} maxLength={6}
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
              data-testid="register-pin-input"
              className="h-11 tracking-widest text-lg"
              placeholder="••••"
              autoComplete="new-password"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pin-confirm" className="text-xs font-bold uppercase tracking-wide">
              Confirme ton PIN
            </Label>
            <Input
              id="pin-confirm" type="password" inputMode="numeric" required minLength={4} maxLength={6}
              value={pinConfirm}
              onChange={(e) => setPinConfirm(e.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
              data-testid="register-pin-confirm-input"
              className="h-11 tracking-widest text-lg"
              placeholder="••••"
              autoComplete="new-password"
            />
          </div>

          <Button
            type="submit" disabled={loading}
            data-testid="register-submit"
            className="w-full h-11 font-bold uppercase tracking-wide"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Créer mon compte"}
          </Button>

          <div className="text-sm text-muted-foreground text-center">
            Déjà inscrit ?{" "}
            <Link to="/login" className="font-bold text-foreground hover:text-primary" data-testid="goto-login">
              Se connecter
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
