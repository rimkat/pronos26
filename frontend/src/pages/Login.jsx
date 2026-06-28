import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Trophy, Loader2 } from "lucide-react";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [pseudo, setPseudo] = useState("");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);

  if (user && user.id) return <Navigate to="/dashboard" replace />;

  const handle = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await login(pseudo.trim(), pin);
    setLoading(false);
    if (res.ok) {
      toast.success("Bienvenue !");
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
        <div className="absolute inset-0 bg-gradient-to-br from-black/85 via-black/65 to-primary/40" />
        <div className="relative h-full flex flex-col justify-end p-10 text-white">
          <Trophy className="h-12 w-12 text-primary mb-3" />
          <h2 className="display text-5xl font-black uppercase leading-none tracking-tight">
            Le terrain est<br /> à toi.
          </h2>
          <p className="mt-3 text-white/70 max-w-sm">
            Pronostique chaque match de la Coupe du Monde 2026 et bats tes potes au classement.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12">
        <form
          onSubmit={handle}
          className="w-full max-w-sm space-y-5"
          data-testid="login-form"
        >
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">
              Connexion
            </div>
            <h1 className="display text-3xl sm:text-4xl font-black uppercase tracking-tight mt-1">
              Bon retour
            </h1>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pseudo" className="text-xs font-bold uppercase tracking-wide">
              Pseudo
            </Label>
            <Input
              id="pseudo" type="text" required value={pseudo} autoComplete="username"
              onChange={(e) => setPseudo(e.target.value)}
              data-testid="login-pseudo-input"
              className="h-11"
              placeholder="Ton pseudo"
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
              data-testid="login-pin-input"
              className="h-11 tracking-widest text-lg"
              placeholder="••••"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            data-testid="login-submit"
            className="w-full h-11 font-bold uppercase tracking-wide"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Entrer"}
          </Button>

          <div className="text-sm text-muted-foreground text-center">
            Pas encore inscrit ?{" "}
            <Link to="/register" className="font-bold text-foreground hover:text-primary" data-testid="goto-register">
              Crée ton compte
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
