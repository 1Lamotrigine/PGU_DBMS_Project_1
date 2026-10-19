"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { QuestCircle, CircleState } from "@/components/quest-circle";
import { api, getToken, Level } from "@/services/api";

export default function LevelPage() {
  const params = useParams();
  const router = useRouter();
  const code = String(params.code).toUpperCase();

  const [level, setLevel] = useState<Level | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .levels()
      .then((levels) => {
        const found = levels.find((l) => l.code === code);
        if (!found) {
          setError("Level not found");
          return;
        }
        setLevel(found);
      })
      .catch((e) => setError(e.message));
  }, [code, router]);

  if (error) return <main className="page accent">{error}</main>;
  if (!level) return <main className="page muted">Loading…</main>;

  const missions = [...level.missions].sort((a, b) => a.order_index - b.order_index);
  const currentIndex = missions.findIndex((m) => !m.progress?.is_completed);

  function stateFor(i: number): CircleState {
    // Trust the server-side lock first (sequential unlock within the level).
    if (missions[i].locked) return "locked";
    if (missions[i].progress?.is_completed) return "done";
    if (i === currentIndex) return "current";
    return i < currentIndex ? "done" : "locked";
  }

  return (
    <main className="page">
      <Link href="/dashboard" className="eq-back">
        <ArrowLeft size={16} /> Levels
      </Link>

      <header className="mt-6" style={{ textAlign: "center" }}>
        <h1 className="eq-h1">Level {level.code}</h1>
        <p className="eq-sub">Five focused missions. Each unlocks the next one.</p>
      </header>

      {/* Centered alternating path */}
      <div className="mx-auto mt-12 flex flex-col items-center" style={{ maxWidth: 560 }}>
        {missions.map((mission, i) => {
          const state = stateFor(i);
          const xp = mission.tasks.reduce((s, t) => s + t.xp_reward_first, 0);
          const clickable = state === "done" || state === "current";
          const onRight = i % 2 === 0; // alternate labels left/right for symmetry

          const label = (
            <div style={{ textAlign: onRight ? "left" : "right", maxWidth: 190 }}>
              <div style={{ fontSize: 15, fontWeight: 500 }}>{mission.title}</div>
              <div className="eq-label mt-0.5">
                {mission.progress?.is_completed ? (
                  <>Completed · {xp} XP</>
                ) : state === "current" ? (
                  <span className="accent" style={{ fontWeight: 500 }}>
                    Start →
                  </span>
                ) : (
                  "Locked"
                )}
              </div>
            </div>
          );

          return (
            <div key={mission.id} className="flex w-full flex-col items-center">
              <div className="flex w-full items-center justify-center gap-5">
                <div style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
                  {onRight ? null : label}
                </div>
                <QuestCircle
                  state={state}
                  content={mission.order_index}
                  size={64}
                  label={mission.title}
                  onClick={clickable ? () => router.push(`/missions/${mission.id}`) : undefined}
                />
                <div style={{ flex: 1, display: "flex", justifyContent: "flex-start" }}>
                  {onRight ? label : null}
                </div>
              </div>

              {i < missions.length - 1 && <div className="eq-dash-v" style={{ height: 34 }} />}
            </div>
          );
        })}

        {missions.length === 0 && <p className="muted">No missions in this level yet.</p>}
      </div>
    </main>
  );
}
