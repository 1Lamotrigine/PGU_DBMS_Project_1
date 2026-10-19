"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { QuestCircle, CircleState } from "@/components/quest-circle";
import { api, getToken, LeaderboardEntry, Level, Progress, UserProfile } from "@/services/api";

const LEVEL_META: { code: string; label: string }[] = [
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
  const [board, setBoard] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    Promise.all([api.me(), api.myProgress(), api.levels(), api.leaderboard(10)])
      .then(([me, pr, lv, lb]) => {
        setProfile(me);
        setProgress(pr);
        setLevels(lv);
        setBoard(lb);
      })
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) return <main className="page accent">{error}</main>;
  if (!profile || !progress) return <main className="page muted">Loading…</main>;

  const currentCode = profile.cefr_level;
  const unlockedRank = progress.unlocked_level_rank ?? 0;
  const currentIndex = LEVEL_META.findIndex((l) => l.code === currentCode);

  // A level is "done" only if it is below the calibrated level; the calibrated
  // level itself is "current"; everything above the unlocked rank is locked.
  function stateFor(_code: string, index: number): CircleState {
    if (index < currentIndex) return "done";
    if (index === currentIndex) return "current";
    if (index <= unlockedRank) return "current";
    return "locked";
  }

  const levelByCode: Record<string, Level | undefined> = {};
  for (const l of levels) levelByCode[l.code] = l;
  const currentLevel = levelByCode[currentCode];
  const currentCompleted = currentLevel
    ? currentLevel.missions.filter((m) => m.progress?.is_completed).length
    : 0;
  const currentTotal = currentLevel ? currentLevel.missions.length : 0;

  const unlockedCode = LEVEL_META[unlockedRank]?.code ?? currentCode;

  return (
    <main className="page">
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ width: "100%", minWidth: 320 }}>
          <header style={{ textAlign: "center" }}>
            <h1 className="eq-h1">Choose your level</h1>
            <p className="eq-sub">Follow the path from A1 to C2.</p>
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
                        <div className="eq-label" style={{ whiteSpace: "nowrap", fontSize: 11 }}>
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
          <div className="mx-auto mt-20 grid gap-4 sm:grid-cols-3" style={{ maxWidth: 640 }}>
            <StatCard value={progress.total_xp} label="Total XP" color="var(--eq-coral)" />
            <StatCard value={`${currentCode}`} label="Your level" color="var(--eq-mint)" />
            <StatCard
              value={`${currentCompleted}/${currentTotal}`}
              label="Missions done"
              color="var(--eq-sun)"
            />
          </div>

          <div className="mx-auto mt-10 flex justify-center">
            <button className="btn-eq" onClick={() => router.push(`/levels/${unlockedCode}`)}>
              Continue {unlockedCode}
            </button>
          </div>
          <p className="eq-caption mt-3" style={{ textAlign: "center" }}>
            Tap a level to open it.
          </p>
        </div>

        {/* Leaderboard — half the container width, centered, visible to everyone */}
        <aside style={{ width: "50%", minWidth: 280, marginTop: 48 }}>
          <section className="eq-card" style={{ padding: 18 }}>
            <h2 className="eq-h1" style={{ fontSize: 20, marginBottom: 12, textAlign: "center" }}>
              Leaderboard
            </h2>
            <p className="eq-caption" style={{ marginTop: -8, marginBottom: 12, textAlign: "center" }}>
              Top students by XP
            </p>
            {board.length === 0 ? (
              <p className="eq-caption" style={{ margin: 0 }}>
                No players yet.
              </p>
            ) : (
              <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 8 }}>
                {board.map((entry) => {
                  const isMe = entry.name === `${profile.firstName} ${profile.lastName}`.trim();
                  return (
                    <li
                      key={entry.rank}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        padding: "6px 8px",
                        borderRadius: 10,
                        background: isMe ? "var(--eq-bg)" : "transparent",
                      }}
                    >
                      <span
                        className="eq-label"
                        style={{
                          width: 24,
                          textAlign: "center",
                          fontWeight: 700,
                          color: entry.rank <= 3 ? "var(--eq-accent)" : "var(--eq-muted)",
                        }}
                      >
                        {entry.rank}
                      </span>
                      <span style={{ flex: 1, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {entry.name}
                        {isMe ? " (you)" : ""}
                      </span>
                      <span className="eq-label" style={{ fontWeight: 700 }}>
                        {entry.total_xp}
                      </span>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
        </aside>
      </div>
    </main>
  );
}

function StatCard({ value, label, color }: { value: string | number; label: string; color: string }) {
  return (
    <div
      className="eq-card"
      style={{ background: "var(--eq-bg)", borderColor: color, textAlign: "center", padding: 20 }}
    >
      <div style={{ fontFamily: "var(--head)", fontWeight: 900, fontSize: 34, color }}>{value}</div>
      <div className="eq-label mt-1">{label}</div>
    </div>
  );
}

