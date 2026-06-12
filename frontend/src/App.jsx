import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "@/components/ui/sonner";
import NavBar from "@/components/NavBar";
import MatchesPage from "@/pages/Matches";
import LoginPage from "@/pages/Login";
import RegisterPage from "@/pages/Register";
import DashboardPage from "@/pages/Dashboard";
import LeaderboardPage from "@/pages/Leaderboard";
import LeaguesPage from "@/pages/Leagues";
import GamePage from "@/pages/Game";

function AppContent() {
  const { user } = useAuth();
  const isAuthed = user && user.id;

  return (
    <div className={`App min-h-screen bg-background ${isAuthed ? "pb-16 sm:pb-0" : ""}`}>
      <NavBar />
      <Routes>
        <Route path="/" element={<MatchesPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/classement" element={<LeaderboardPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route path="/ligues" element={<LeaguesPage />} />
        <Route path="/jeu" element={<GamePage />} />
      </Routes>
      <Toaster position="top-right" richColors />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
