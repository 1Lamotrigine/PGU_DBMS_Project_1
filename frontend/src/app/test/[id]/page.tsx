"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Trophy } from "lucide-react";

import { ResultScreen } from "@/components/result-screen";
import { api, getToken, Mission, Question } from "@/services/api";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export default function TestPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);

  const [mission, setMission] = useState<Mission | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, { option_id?: number; text?: string }>>({});
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
        setQuestions(
          m.tasks
            .filter((t) => ["multiple_choice", "fill_blank", "image_match"].includes(t.type))
            .flatMap((t) => t.questions ?? []),
        );
      })
      .catch((e) => setError(e.message));
  }, [missionId, router]);

  async function submit() {
    setSubmitting(true);
    try {
      const payload = questions.map((q) => {
        const a = answers[q.id];
        if (a?.text != null) return { question_id: q.id, text: a.text };
        return { question_id: q.id, option_id: a?.option_id };
      });
      const res = await api.submitTests(missionId, payload);
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
  const answeredTotal = Object.values(answers).filter(
    (a) => a.option_id != null || (a.text ?? "").trim() !== "",
  ).length;
  const current = questions[step];
  const picked = current ? answers[current.id] : undefined;
  const isTextAnswer =
    current?.question_type === "fill_blank" || current?.question_type === "translation";
  const currentAnswered = isTextAnswer
    ? (picked?.text ?? "").trim() !== ""
    : picked?.option_id != null;
  const isLast = step >= total - 1;
  const allAnswered = answeredTotal === total;

  return (
    <main className="page" style={{ maxWidth: 860 }}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/missions/${missionId}`} className="eq-back">
          <ArrowLeft size={16} /> Lesson
        </Link>
        <div className="flex items-center gap-2">
          <span className="eq-pill eq-pill--mint">
            <Trophy size={15} /> {answeredTotal}/{total}
          </span>
        </div>
      </div>

      {total === 0 ? (
        <div className="eq-grammar-stage">
          <div className="eq-grammar-stage__head">
            <p className="muted" style={{ margin: 0 }}>
              No questions in this mission yet.
            </p>
          </div>
        </div>
      ) : (
        <>
          <div className="eq-grammar-stage eq-test-stage">
            <div className="eq-grammar-stage__head">
              <span className="eq-quiz__badge">
                Question {step + 1} of {total}
              </span>
              <h1 className="eq-grammar-q" key={`q-${current.id}`}>
                {current.question_text}
              </h1>
              <p className="eq-caption" style={{ margin: 0 }}>
                Pick the correct answer to continue.
              </p>
            </div>

            {isTextAnswer ? (
              <div className="eq-test-input-wrap" key={`input-${current.id}`}>
                <input
                  className="eq-input eq-test-input"
                  placeholder="Type your answer"
                  value={picked?.text ?? ""}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, [current.id]: { text: e.target.value } }))
                  }
                />
              </div>
            ) : (
              <div className="eq-grammar-words" key={`w-${current.id}`}>
                {current.options.map((o, i) => {
                  const active = picked?.option_id === o.id;
                  return (
                    <button
                      key={o.id}
                      type="button"
                      className={`eq-grammar-word eq-test-word ${active ? "selected" : ""}`}
                      style={{ animationDelay: `${i * 40}ms` }}
                      onClick={() =>
                        setAnswers((prev) => ({ ...prev, [current.id]: { option_id: o.id } }))
                      }
                      aria-pressed={active}
                    >
                      <span className="eq-test-word__key">{LETTERS[i] ?? i + 1}</span>
                      <span className="eq-test-word__text">{o.option_text}</span>
                      {active && (
                        <span className="eq-grammar-word__mark">
                          <Check size={18} />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="eq-grammar-status" aria-live="polite">
              {!isTextAnswer && (
                <span className={picked?.option_id != null ? "eq-grammar-ok" : ""}>
                  {picked?.option_id != null ? "Answer selected" : "Choose one option"}
                </span>
              )}
            </div>
          </div>

          <div className="eq-progress mt-5">
            <span style={{ width: `${total ? ((step + 1) / total) * 100 : 0}%` }} />
          </div>

          <div className="eq-dots mt-6">
            {questions.map((q, i) => {
              const a = answers[q.id];
              const on = Boolean(a && (a.option_id != null || (a.text ?? "").trim() !== ""));
              return <span key={q.id} className={`eq-dot ${on ? "on" : ""} ${i === step ? "cur" : ""}`} />;
            })}
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
                disabled={!currentAnswered}
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
