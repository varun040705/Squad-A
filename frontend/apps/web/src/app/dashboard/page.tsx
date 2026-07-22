"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import PageContainer from "@/components/layout/PageContainer";

import { useAuth } from "@/contexts/AuthContext";
import {
  AuthService,
  UserResponse,
} from "@/features/auth/services/auth.service";

export default function DashboardPage() {
  const {
    accessToken,
    loading,
    logout,
  } = useAuth();

  const router = useRouter();

  const [user, setUser] = useState<UserResponse | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !accessToken) {
      router.replace("/login");
    }
  }, [loading, accessToken, router]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    async function fetchUser() {
      try {
        const currentUser = await AuthService.me();

        setUser(currentUser);
      } catch (err) {
        console.error(err);

        setError("Unable to load user information.");
      } finally {
        setLoadingUser(false);
      }
    }

    fetchUser();
  }, [accessToken]);

  if (loading || loadingUser) {
    return <p>Loading...</p>;
  }

  if (!accessToken) {
    return null;
  }

  return (
    <>
      <Header />

      <PageContainer>
        <h1>Dashboard</h1>

        {error && <p>{error}</p>}

        {user && (
          <>
            <h2>Welcome, {user.username}</h2>

            <p>
              <strong>Full Name:</strong> {user.full_name}
            </p>

            <p>
              <strong>Email:</strong> {user.email}
            </p>

            <p>
              <strong>Role:</strong> {user.role}
            </p>

            <p>
              <strong>Verified:</strong>{" "}
              {user.is_verified ? "Yes" : "No"}
            </p>
          </>
        )}

        <button
          onClick={() => {
            logout();
            router.replace("/login");
          }}
          style={{
            padding: "10px 20px",
            cursor: "pointer",
            marginTop: "20px",
          }}
        >
          Logout
        </button>
      </PageContainer>

      <Footer />
    </>
  );
}