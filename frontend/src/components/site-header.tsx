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
      style={{ background: "var(--eq-bg)", borderBottom: "1px solid var(--eq-border)" }}
    >
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-6 py-3">
        <Link href={profile ? "/dashboard" : "/"} className="flex items-center gap-3">
          <span
            aria-hidden
            style={{
              width: 32,
              height: 32,
              borderRadius: 20,
              background: "var(--eq-accent)",
            }}
          />
          <span style={{ fontWeight: 500, fontSize: 16 }}>English Quest</span>
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
            <button onClick={logout} className="muted text-sm">
              Log out
            </button>
          ) : (
            <Link href="/login" className="muted text-sm">
              Log in
            </Link>
          )}

          <button
            onClick={toggle}
            aria-label="Toggle theme"
            title={theme === "dark" ? "Light theme" : "Dark theme"}
            className="flex items-center justify-center"
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              border: "1px solid var(--eq-border)",
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
