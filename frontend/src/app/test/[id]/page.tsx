"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";

import { ResultScreen } from "@/components/result-screen";
import { api, getToken, Mission, Question } from "@/services/api";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export default function TestPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);

  const [mission, setMission] = useState<Mission | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ percent: number; passed: boolean } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .mission(missionId)
      .then((m) => {
        setMission(m);
        setQuestions(m.tasks.filter((t) => t.type === "multiple_choice").flatMap((t) => t.questions ?? []));
      })
      .catch((e) => setError(e.message));
  }, [missionId, router]);

  async function submit() {
    setSubmitting(true);
    try {
      const correct = questions.filter((q) => {
        const correctOption = q.options.find((o) => o.is_correct);
        return correctOption && answers[q.id] === correctOption.id;
      }).length;
      const res = await api.submitTests(missionId, correct, questions.length);
      setResult({ percent: res.percent, passed: res.passed });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <main className="page accent">{error}</main>;
  if (!mission) return <main className="page muted">Loading…</main>;

  if (result) {
    return (
      <ResultScreen
        success={result.passed}
        percent={result.percent}
        onRetry={() => {
          setResult(null);
          setAnswers({});
          setStep(0);
        }}
        backHref={`/missions/${missionId}`}
      />
    );
  }

  const total = questions.length;
  const answeredTotal = Object.keys(answers).length;
  const current = questions[step];
  const picked = current ? answers[current.id] : undefined;
  const isLast = step >= total - 1;
  const allAnswered = answeredTotal === total;

  return (
    <main className="page" style={{ maxWidth: 640 }}>
      <Link href={`/missions/${missionId}`} className="eq-back">
        <ArrowLeft size={16} /> Lesson
      </Link>

      <div className="mt-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="eq-h1">Test</h1>
          <p className="eq-sub" style={{ marginTop: 4 }}>
            Pick one answer for each question.
          </p>
        </div>
        <span className="eq-pill--sun eq-pill" style={{ flex: "none" }}>
          {total ? step + 1 : 0} / {total}
        </span>
      </div>

      <div className="eq-progress mt-5">
        <span style={{ width: `${total ? ((step + 1) / total) * 100 : 0}%` }} />
      </div>

      {total === 0 ? (
        <div className="eq-quiz mt-6">
          <p className="muted" style={{ margin: 0 }}>
            No questions in this mission yet.
          </p>
        </div>
      ) : (
        <>
          <section className="eq-quiz mt-6">
            <span className="eq-quiz__badge">Question {step + 1}</span>
            <h2 className="eq-quiz__q">{current.question_text}</h2>

            <div className="grid gap-2.5">
              {current.options.map((o, i) => {
                const active = picked === o.id;
                return (
                  <button
                    key={o.id}
                    type="button"
                    className={`eq-opt ${active ? "selected" : ""}`}
                    onClick={() => setAnswers((prev) => ({ ...prev, [current.id]: o.id }))}
                    aria-pressed={active}
                  >
                    <span className="eq-opt__key">{LETTERS[i] ?? i + 1}</span>
                    <span className="eq-opt__text">{o.option_text}</span>
                    <span className="eq-opt__check">
                      <Check size={20} strokeWidth={2.5} />
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <div className="eq-dots mt-6">
            {questions.map((q, i) => (
              <span
                key={q.id}
                className={`eq-dot ${answers[q.id] != null ? "on" : ""} ${i === step ? "cur" : ""}`}
              />
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between gap-3">
            <button
              className="btn-eq-ghost"
              type="button"
              disabled={step === 0}
              onClick={() => setStep((s) => Math.max(0, s - 1))}
            >
              <ArrowLeft size={16} /> Back
            </button>

            {isLast ? (
              <button
                className="btn-eq"
                type="button"
                disabled={!allAnswered || submitting}
                onClick={submit}
              >
                {submitting ? "Submitting…" : "Submit test"}
              </button>
            ) : (
              <button
                className="btn-eq"
                type="button"
                disabled={picked == null}
                onClick={() => setStep((s) => Math.min(total - 1, s + 1))}
              >
                Next <ArrowRight size={16} />
              </button>
            )}
          </div>
        </>
      )}
    </main>
  );
}
