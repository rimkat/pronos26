import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "@/components/ui/sonner";
import NavBar from "@/components/NavBar";
import MatchesPage from "@/pages/Matches";
import LoginPage from "@/pages/Login";
import RegisterPage from "@/pages/Register";
import DashboardPage from "@/pages/Dashboard";
import LeaderboardPage from "@/pages/Leaderboard";

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="App min-h-screen bg-background">
            <NavBar />
            <Routes>
              <Route path="/" element={<MatchesPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/classement" element={<LeaderboardPage />} />
              <Route path="/leaderboard" element={<LeaderboardPage />} />
            </Routes>
            <Toaster position="top-right" richColors />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
