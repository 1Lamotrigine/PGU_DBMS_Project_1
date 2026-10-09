"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/components/theme-provider";
import { api, clearToken, getToken, UserProfile } from "@/services/api";

export function SiteHeader() {
  const router = useRouter();
  const { theme, toggle } = useTheme();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    function load() {
      if (!getToken()) {
        setProfile(null);
        return;
      }
      api.me().then(setProfile).catch(() => setProfile(null));
    }
    load();
    window.addEventListener("eq-auth-changed", load);
    return () => window.removeEventListener("eq-auth-changed", load);
  }, []);

  function logout() {
    clearToken();
    setProfile(null);
    router.replace("/login");
  }

  return (
    <header
      className="sticky top-0 z-30"
      style={{ background: "var(--eq-bg)", borderBottom: "2px solid var(--eq-border)" }}
    >
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-6 py-3">
        <Link href={profile ? "/dashboard" : "/"} className="flex items-center gap-3">
          <span
            aria-hidden
            style={{
              width: 30,
              height: 24,
              borderRadius: "10px 10px 10px 2px",
              background: "var(--eq-sun)",
              boxShadow: "0 8px 18px -10px var(--eq-sun)",
            }}
          />
          <span
            className="font-display"
            style={{ fontWeight: 800, fontSize: 18, letterSpacing: "-0.02em" }}
          >
            English&nbsp;Quest
          </span>
        </Link>

        <nav className="flex items-center gap-5">
          {profile && (
            <Link href="/dashboard" className="muted hidden text-sm sm:inline">
              Dashboard
            </Link>
          )}
          {profile?.role === "teacher" && (
            <Link href="/admin/missions" className="muted hidden text-sm sm:inline">
              Admin
            </Link>
          )}
          {profile ? (
            <button onClick={logout} className="btn-eq-ghost" style={{ minHeight: 38, padding: "0 18px" }}>
              Log out
            </button>
          ) : (
            <Link href="/login" className="btn-eq" style={{ minHeight: 38, padding: "0 20px" }}>
              Log in
            </Link>
          )}

          <button
            onClick={toggle}
            aria-label="Toggle theme"
            title={theme === "dark" ? "Light theme" : "Dark theme"}
            className="flex items-center justify-center"
            style={{
              width: 38,
              height: 38,
              borderRadius: 999,
              border: "2px solid var(--eq-border)",
              color: "var(--eq-muted)",
              background: "transparent",
            }}
          >
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </nav>
      </div>
    </header>
  );
}
