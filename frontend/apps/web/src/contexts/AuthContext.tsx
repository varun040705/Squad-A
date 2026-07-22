"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

import { AuthService } from "@/features/auth/services/auth.service";

type AuthContextType = {
  accessToken: string | null;
  refreshToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [accessToken, setAccessToken] = useState<string | null>(
    null
  );

  const [refreshToken, setRefreshToken] = useState<string | null>(
    null
  );

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const access = localStorage.getItem("access_token");
    const refresh = localStorage.getItem("refresh_token");

    setAccessToken(access);
    setRefreshToken(refresh);

    setLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const response: any = await AuthService.login({
      email,
      password,
    });

    setAccessToken(response.access_token);
    setRefreshToken(response.refresh_token);

    localStorage.setItem(
      "access_token",
      response.access_token
    );

    localStorage.setItem(
      "refresh_token",
      response.refresh_token
    );
  }

  function logout() {
    setAccessToken(null);
    setRefreshToken(null);

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        refreshToken,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}