import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking | false = anon | object = logged
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    const token = localStorage.getItem("wc2026_token");
    if (!token) {
      setUser(false);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      localStorage.removeItem("wc2026_token");
      setUser(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshMe();
  }, [refreshMe]);

  const login = async (pseudo, pin) => {
    try {
      const { data } = await api.post("/auth/login", { pseudo, pin });
      localStorage.setItem("wc2026_token", data.token);
      setUser(data.user);
      return { ok: true };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  };

  const register = async (pseudo, pin) => {
    try {
      const { data } = await api.post("/auth/register", { pseudo, pin });
      localStorage.setItem("wc2026_token", data.token);
      setUser(data.user);
      return { ok: true };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  };

  const logout = () => {
    localStorage.removeItem("wc2026_token");
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
