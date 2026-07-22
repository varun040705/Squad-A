"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import PageContainer from "@/components/layout/PageContainer";

import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleLogin() {
  try {
    console.log("1. Before login");

    await login(email, password);

    console.log("2. Login completed");

    router.push("/dashboard");

    console.log("3. Redirect called");
  } catch (error) {
    console.error(error);
    alert("Login Failed");
  }
}

  return (
    <>
      <Header />

      <PageContainer>
        <h1>Login</h1>

        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          style={{
            display: "block",
            marginBottom: 12,
            padding: 10,
            width: 300,
          }}
        />

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          style={{
            display: "block",
            marginBottom: 12,
            padding: 10,
            width: 300,
          }}
        />

        <button
          onClick={handleLogin}
          style={{
            padding: "10px 20px",
            cursor: "pointer",
          }}
        >
          Login
        </button>
      </PageContainer>

      <Footer />
    </>
  );
}