"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { QuestCircle, CircleState } from "@/components/quest-circle";
import { api, getToken, Level, Progress, UserProfile } from "@/services/api";

const LEVEL_META: { code: string; label: string }[] = [
  { code: "A0", label: "Starter" },
  { code: "A1", label: "Beginner" },
  { code: "A2", label: "Elementary" },
  { code: "B1", label: "Intermediate" },
  { code: "B2", label: "Upper-int." },
  { code: "C1", label: "Advanced" },
  { code: "C2", label: "Proficient" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [levels, setLevels] = useState<Level[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    Promise.all([api.me(), api.myProgress(), api.levels()])
      .then(([me, pr, lv]) => {
        setProfile(me);
        setProgress(pr);
        setLevels(lv);
      })
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) return <main className="page accent">{error}</main>;
  if (!profile || !progress) return <main className="page muted">Loading…</main>;

  const currentCode = profile.cefr_level;
  const currentIndex = LEVEL_META.findIndex((l) => l.code === currentCode);

  function stateFor(_code: string, index: number): CircleState {
    if (index < currentIndex) return "done";
    if (index === currentIndex) return "current";
    return "locked";
  }

  const levelByCode: Record<string, Level | undefined> = {};
  for (const l of levels) levelByCode[l.code] = l;
  const currentLevel = levelByCode[currentCode];

  return (
    <main className="page">
      <header style={{ textAlign: "center" }}>
        <h1 className="eq-h1">Choose your level</h1>
        <p className="eq-sub">Follow the path from A0 to C2.</p>
      </header>

      {/* Horizontal wavy path — centered, scrollable on small screens */}
      <div className="mt-16" style={{ display: "flex", justifyContent: "center" }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            maxWidth: "100%",
            overflowX: "auto",
            margin: "0 auto",
            padding: "8px 4px 4px",
          }}
        >
          {LEVEL_META.map((meta, i) => {
            const state = stateFor(meta.code, i);
            const offset = i % 2 === 0 ? 0 : 20;
            const locked = state === "locked";
            return (
              <div key={meta.code} style={{ display: "flex", alignItems: "flex-start", flexShrink: 0 }}>
                {/* circle + label move together as one unit */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    transform: `translateY(${offset}px)`,
                    width: 68,
                  }}
                >
                  <QuestCircle
                    state={state}
                    content={meta.code}
                    size={state === "current" ? 60 : 54}
                    label={meta.label}
                    onClick={locked ? undefined : () => router.push(`/levels/${meta.code}`)}
                  />
                  <div style={{ marginTop: 10, textAlign: "center" }}>
                    <div
                      className="eq-label"
                      style={{ whiteSpace: "nowrap", fontSize: 11 }}
                    >
                      {meta.label}
                    </div>
                    <div
                      className="eq-label"
                      style={{
                        fontSize: 11,
                        fontWeight: 500,
                        color: state === "current" ? "var(--eq-accent)" : "transparent",
                      }}
                    >
                      You are here
                    </div>
                  </div>
                </div>
                {i < LEVEL_META.length - 1 && (
                  <div className="eq-dash-h" style={{ width: 26, marginTop: 28 }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom stats + continue */}
      <div className="mx-auto mt-20 flex flex-wrap items-center justify-center gap-6">
        <div className="eq-caption">
          Level {currentCode} · {progress.total_xp} XP ·{" "}
          {currentLevel ? progress.completed_missions : 0} of {currentLevel?.missions.length ?? 0} missions done
        </div>
        <button className="btn-eq" onClick={() => router.push(`/levels/${currentCode}`)}>
          Continue {currentCode}
        </button>
      </div>
      <p className="eq-caption mt-3" style={{ textAlign: "center" }}>
        Tap a level to open it.
      </p>
    </main>
  );
}
