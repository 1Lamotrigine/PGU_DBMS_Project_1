"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { api, setToken } from "@/services/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { token } = await api.login({ email, password });
      setToken(token);
      router.push("/dashboard");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function onGoogleCredential(credential: string) {
    setError("");
    setLoading(true);
    try {
      const { token, user } = await api.googleLogin(credential);
      setToken(token);
      router.push(user.is_calibrated ? "/dashboard" : "/calibration");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page" style={{ maxWidth: 400 }}>
      <h1 className="eq-h1">Log in</h1>
      <p className="eq-sub">Welcome back to English Quest.</p>

      <form onSubmit={onSubmit} className="mt-8 grid gap-4">
        <label className="grid gap-1.5">
          <span className="eq-label">Email</span>
          <input
            type="email"
            autoComplete="email"
            className="eq-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            className="eq-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && <p className="eq-caption" style={{ color: "var(--eq-text)" }}>{error}</p>}

        <button className="btn-eq w-full" disabled={loading}>
          {loading ? "Signing in…" : "Log in"}
        </button>
      </form>

      <div className="mt-7 grid gap-4">
        <div className="flex items-center gap-3">
          <span style={{ height: 2, flex: 1, background: "var(--eq-border)" }} />
          <span className="eq-caption">or</span>
          <span style={{ height: 2, flex: 1, background: "var(--eq-border)" }} />
        </div>
        <GoogleSignInButton onCredential={onGoogleCredential} disabled={loading} />
      </div>

      <p className="eq-caption mt-6">
        No account?{" "}
        <Link href="/register" className="accent">
          Create one
        </Link>
      </p>
    </main>
  );
}
