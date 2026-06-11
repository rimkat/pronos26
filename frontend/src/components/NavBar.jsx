import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";
import { Trophy, LayoutDashboard, ListOrdered, Sun, Moon, LogOut, LogIn } from "lucide-react";

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

  return (
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

        <nav className="flex items-center gap-1">
          <NavLink to="/" label="Matchs" icon={Trophy} testid="nav-matches" />
          {user && user.id && (
            <>
              <NavLink to="/dashboard" label="Tableau" icon={LayoutDashboard} testid="nav-dashboard" />
              <NavLink to="/classement" label="Classement" icon={ListOrdered} testid="nav-leaderboard" />
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
          {user && user.id ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => { logout(); navigate("/login"); }}
              data-testid="nav-logout"
              className="font-bold uppercase tracking-wide text-xs"
            >
              <LogOut className="h-3.5 w-3.5 mr-1.5" /> Sortir
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={() => navigate("/login")}
              data-testid="nav-login"
              className="font-bold uppercase tracking-wide text-xs"
            >
              <LogIn className="h-3.5 w-3.5 mr-1.5" /> Connexion
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
