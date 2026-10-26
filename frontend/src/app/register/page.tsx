"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { api, setToken } from "@/services/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ firstName: "", lastName: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { token } = await api.register(form);
      setToken(token);
      router.push("/calibration");
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
      // New Google users start uncalibrated; linked accounts keep their level.
      router.push(user.is_calibrated ? "/dashboard" : "/calibration");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page" style={{ maxWidth: 440 }}>
      <h1 className="eq-h1">Create account</h1>
      <p className="eq-sub">At least 8 characters, one uppercase letter and one digit.</p>

      <form onSubmit={onSubmit} className="mt-8 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="eq-label">First name</span>
            <input className="eq-input" value={form.firstName} onChange={(e) => update("firstName", e.target.value)} required />
          </label>
          <label className="grid gap-1.5">
            <span className="eq-label">Last name</span>
            <input className="eq-input" value={form.lastName} onChange={(e) => update("lastName", e.target.value)} required />
          </label>
        </div>
        <label className="grid gap-1.5">
          <span className="eq-label">Email</span>
          <input type="email" className="eq-input" value={form.email} onChange={(e) => update("email", e.target.value)} required />
        </label>
        <label className="grid gap-1.5">
          <span className="eq-label">Password</span>
          <input type="password" className="eq-input" value={form.password} onChange={(e) => update("password", e.target.value)} required />
        </label>

        {error && <p className="eq-caption" style={{ color: "var(--eq-text)" }}>{error}</p>}

        <button className="btn-eq w-full" disabled={loading}>
          {loading ? "Creating…" : "Create account"}
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
        Already registered?{" "}
        <Link href="/login" className="accent">
          Log in
        </Link>
      </p>
    </main>
  );
}
