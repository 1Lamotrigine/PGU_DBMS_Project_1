"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Check, Lock } from "lucide-react";

import { api, getToken, Mission } from "@/services/api";

type ModuleDef = {
  key: "test" | "pronunciation" | "game" | "grammar";
  title: string;
  description: string;
  href: (id: number) => string;
};

const MODULES: ModuleDef[] = [
  {
    key: "test",
    title: "Test",
    description: "5 multiple-choice questions",
    href: (id) => `/test/${id}`,
  },
  {
    key: "pronunciation",
    title: "Pronunciation",
    description: "Say the English words out loud",
    href: (id) => `/pronounce/${id}`,
  },
  {
    key: "game",
    title: "Dictionary game",
    description: "Look at the picture — say the English word",
    href: (id) => `/game/${id}`,
  },
  {
    key: "grammar",
    title: "Grammar game",
    description: "Catch the correct word form — tap an answer",
    href: (id) => `/grammar/${id}`,
  },
];

const CIRCLE = 84;

export default function MissionPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);
  const [mission, setMission] = useState<Mission | null>(null);
  const [levelCode, setLevelCode] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    Promise.all([api.mission(missionId), api.levels()])
      .then(([m, levels]) => {
        setMission(m);
        const lvl = levels.find((l) => l.id === m.level_id);
        setLevelCode(lvl?.code ?? "");
      })
      .catch((e) => setError(e.message));
  }, [missionId, router]);

  if (error) return <main className="page accent">{error}</main>;
  if (!mission) return <main className="page muted">Loading…</main>;

  const completed = Boolean(mission.progress?.is_completed);
  const testsPassed = completed || Boolean(mission.progress?.tests_passed);
  const pronunciationPassed = completed || Boolean(mission.progress?.pronunciation_passed);
  const gamePassed = completed || Boolean(mission.progress?.game_passed);
  const grammarPassed = Boolean(mission.progress?.grammar_passed);

  const status = (key: ModuleDef["key"]) => {
    if (key === "test") return testsPassed ? "done" : "current";
    if (key === "pronunciation") return pronunciationPassed ? "done" : testsPassed ? "current" : "locked";
    if (key === "game") return gamePassed ? "done" : pronunciationPassed ? "current" : "locked";
    return grammarPassed ? "done" : gamePassed ? "current" : "locked";
  };

  return (
    <main className="page">
      <Link href={`/levels/${levelCode || ""}`} className="eq-back">
        <ArrowLeft size={16} /> Level {levelCode}
      </Link>

      <header className="mt-6" style={{ textAlign: "center" }}>
        <h1 className="eq-h1">{mission.title}</h1>
        <p className="eq-sub">Complete the modules in order. Each unlocks the next one.</p>
      </header>

      {/* Centered vertical path */}
      <div className="mx-auto mt-12 flex flex-col items-center" style={{ maxWidth: 420 }}>
        {MODULES.map((m, i) => {
          const st = status(m.key);
          const clickable = st === "done" || st === "current";
          const locked = st === "locked";
          return (
            <div key={m.key} className="flex w-full flex-col items-center">
              <button
                type="button"
                className={`eq-circle ${st}`}
                style={{ width: CIRCLE, height: CIRCLE }}
                disabled={!clickable}
                onClick={clickable ? () => router.push(m.href(missionId)) : undefined}
                aria-label={m.title}
              >
                {st === "done" ? (
                  <Check size={34} />
                ) : st === "locked" ? (
                  <Lock size={30} strokeWidth={1.75} />
                ) : (
                  <span style={{ width: 12, height: 12, borderRadius: "50%", background: "#fff" }} />
                )}
              </button>

              <div style={{ textAlign: "center", marginTop: 12, maxWidth: 300 }}>
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 500,
                    color: locked ? "var(--eq-muted)" : "var(--eq-text)",
                  }}
                >
                  {m.title}
                </div>
                <div className="eq-caption" style={{ marginTop: 2 }}>
                  {m.description}
                </div>
              </div>

              {i < MODULES.length - 1 && <div className="eq-dash-v" style={{ height: 40 }} />}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-10 flex items-center justify-center gap-6">
        <span className="eq-label flex items-center gap-2">
          <span style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--eq-accent)" }} />
          Available
        </span>
        <span className="eq-label flex items-center gap-2">
          <Lock size={14} /> Locked
        </span>
      </div>
    </main>
  );
}
