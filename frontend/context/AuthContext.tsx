"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "@/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check initial user from localStorage or /auth/me
    const initAuth = async () => {
      try {
        const cachedUser = api.getCurrentUser();
        if (cachedUser) {
          setUser(cachedUser);
        }
        // Verify token with backend
        const token = typeof window !== "undefined" ? localStorage.getItem("sourcelearn_token") : null;
        if (token) {
          const freshUser = await api.getMe();
          setUser(freshUser);
          if (typeof window !== "undefined") {
            localStorage.setItem("sourcelearn_user", JSON.stringify(freshUser));
          }
        }
      } catch (err) {
        // Token invalid or expired
        api.logout();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.login({ email, password });
    setUser(res.user);
  };

  const register = async (email: string, name: string, password: string) => {
    const res = await api.register({ email, name, password });
    setUser(res.user);
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
