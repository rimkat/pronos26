import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";
import { Trophy, LayoutDashboard, ListOrdered, Sun, Moon, LogOut, LogIn, Users, Gamepad2 } from "lucide-react";

export default function NavBar() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const NavLink = ({ to, label, icon: Icon, testid }) => {
    const active = location.pathname === to;
    return (
      <Link
        to={to}
        data-testid={testid}
        className={`flex items-center gap-1.5 text-xs sm:text-sm font-bold uppercase tracking-wide transition-colors px-2.5 py-1.5 rounded ${
          active ? "text-foreground bg-secondary" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Icon className="h-4 w-4" /> <span className="hidden sm:inline">{label}</span>
      </Link>
    );
  };

  const isAuthed = user && user.id;

  return (
    <>
      <header className="sticky top-0 z-50 bg-background/85 backdrop-blur-md border-b border-border">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
            <div className="h-7 w-7 rounded-sm bg-primary flex items-center justify-center">
              <Trophy className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="display font-black text-lg tracking-tight uppercase">
              Pronos<span className="text-primary">26</span>
            </span>
          </Link>

          {/* Sur mobile, si connecté, ces liens basculent dans le bandeau du bas */}
          <nav className={`items-center gap-1 ${isAuthed ? "hidden sm:flex" : "flex"}`}>
            <NavLink to="/" label="Matchs" icon={Trophy} testid="nav-matches" />
            {isAuthed && (
              <>
                <NavLink to="/dashboard" label="Tableau" icon={LayoutDashboard} testid="nav-dashboard" />
                <NavLink to="/ligues" label="Ligues" icon={Users} testid="nav-leagues" />
                <NavLink to="/classement" label="Classement" icon={ListOrdered} testid="nav-leaderboard" />
                <NavLink to="/jeu" label="Jeu" icon={Gamepad2} testid="nav-game" />
              </>
            )}
          </nav>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              data-testid="theme-toggle"
              aria-label="Changer de thème"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            {isAuthed ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => { logout(); navigate("/login"); }}
                data-testid="nav-logout"
                className="font-bold uppercase tracking-wide text-xs"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sortir</span>
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => navigate("/login")}
                data-testid="nav-login"
                className="font-bold uppercase tracking-wide text-xs"
              >
                <LogIn className="h-4 w-4" /> Connexion
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Bandeau sticky en bas, mobile uniquement, pour les utilisateurs connectés */}
      {isAuthed && (
        <nav
          className="sm:hidden fixed bottom-0 inset-x-0 z-50 bg-background/95 backdrop-blur-md border-t border-border flex items-stretch justify-around"
          data-testid="mobile-bottom-nav"
        >
          <BottomLink to="/" label="Matchs" icon={Trophy} testid="bottom-nav-matches" location={location} />
          <BottomLink to="/dashboard" label="Tableau" icon={LayoutDashboard} testid="bottom-nav-dashboard" location={location} />
          <BottomLink to="/ligues" label="Ligues" icon={Users} testid="bottom-nav-leagues" location={location} />
          <BottomLink to="/classement" label="Classement" icon={ListOrdered} testid="bottom-nav-leaderboard" location={location} />
          <BottomLink to="/jeu" label="Jeu" icon={Gamepad2} testid="bottom-nav-game" location={location} />
        </nav>
      )}
    </>
  );
}

function BottomLink({ to, label, icon: Icon, testid, location }) {
  const active = location.pathname === to;
  return (
    <Link
      to={to}
      data-testid={testid}
      className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-bold uppercase tracking-wide transition-colors ${
        active ? "text-primary" : "text-muted-foreground"
      }`}
    >
      <Icon className="h-5 w-5" />
      {label}
    </Link>
  );
}
