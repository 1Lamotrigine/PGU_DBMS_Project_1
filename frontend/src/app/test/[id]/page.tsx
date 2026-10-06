"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { ResultScreen } from "@/components/result-screen";
import { api, getToken, Mission, Question } from "@/services/api";

export default function TestPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);

  const [mission, setMission] = useState<Mission | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
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
        }}
        backHref={`/missions/${missionId}`}
      />
    );
  }

  const total = questions.length;
  const answered = Object.keys(answers).length;

  return (
    <main className="page" style={{ maxWidth: 640 }}>
      <Link href={`/missions/${missionId}`} className="eq-back">
        <ArrowLeft size={16} /> Lesson
      </Link>

      <div className="mt-6 flex items-baseline justify-between">
        <h1 className="eq-h1">Test</h1>
        <span className="eq-caption">
          {answered} / {total}
        </span>
      </div>

      <div className="mt-4 grid gap-7">
        {questions.map((q, i) => (
          <section key={q.id}>
            <p className="mb-3" style={{ fontWeight: 500 }}>
              {i + 1}. {q.question_text}
            </p>
            <div className="grid gap-2">
              {q.options.map((o) => (
                <button
                  key={o.id}
                  className={`eq-choice ${answers[q.id] === o.id ? "selected" : ""}`}
                  onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: o.id }))}
                >
                  {o.option_text}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>

      <button
        className="btn-eq mt-8 w-full"
        disabled={answered < total || submitting}
        onClick={submit}
      >
        Submit test
      </button>
    </main>
  );
}
