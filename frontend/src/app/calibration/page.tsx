"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { api, CalibrationQuestion, getToken } from "@/services/api";

export default function CalibrationPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<CalibrationQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [finished, setFinished] = useState<{ cefr_level: string; total_xp: number } | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api.calibrationQuestions().then(setQuestions).catch((e) => setError(e.message));
  }, [router]);

  const answered = useMemo(() => Object.keys(answers).length, [answers]);
  const total = questions.length;

  async function onSubmit() {
    setError("");
    setLoading(true);
    try {
      const payload = Object.entries(answers).map(([id, selected_option]) => ({
        question_id: Number(id),
        selected_option,
      }));
      const result = await api.calibration(payload);
      setFinished(result);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (finished) {
    return (
      <main className="page text-center" style={{ maxWidth: 480 }}>
        <p className="eq-label">Your level</p>
        <div className="eq-circle current mx-auto my-5" style={{ width: 96, height: 96, fontSize: 28 }}>
          {finished.cefr_level}
        </div>
        <h1 className="eq-h1">Level {finished.cefr_level}</h1>
        <p className="eq-sub">Starting XP: {finished.total_xp}</p>
        <div className="mt-8 flex justify-center">
          <button className="btn-eq" onClick={() => router.push("/dashboard")}>
            Go to dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="page" style={{ maxWidth: 640 }}>
      <div className="flex items-baseline justify-between">
        <h1 className="eq-h1">Placement test</h1>
        <span className="eq-caption">
          {answered} / {total}
        </span>
      </div>
      <p className="eq-sub">Answer all questions to determine your level.</p>

      <div className="mt-8 grid gap-7">
        {questions.map((q, i) => (
          <section key={q.id}>
            <p className="mb-3" style={{ fontWeight: 500 }}>
              {i + 1}. {q.question_text}
            </p>
            <div className="grid gap-2">
              {(["A", "B", "C", "D"] as const).map((key) => (
                <button
                  key={key}
                  className={`eq-choice ${answers[q.id] === key ? "selected" : ""}`}
                  onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: key }))}
                >
                  <span className="eq-label" style={{ width: 16 }}>
                    {key}
                  </span>
                  {q.options[key]}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>

      {error && <p className="eq-caption mt-4" style={{ color: "var(--eq-text)" }}>{error}</p>}

      {total > 0 && (
        <button className="btn-eq mt-8 w-full" disabled={answered < total || loading} onClick={onSubmit}>
          {loading ? "Submitting…" : "Submit placement test"}
        </button>
      )}
    </main>
  );
}
