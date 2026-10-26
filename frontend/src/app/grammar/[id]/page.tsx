"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Check, Heart, Trophy, X } from "lucide-react";

import { ResultScreen } from "@/components/result-screen";
import { useAudioUnlock } from "@/components/use-audio-unlock";
import { api, getToken, GrammarQuestion } from "@/services/api";

const MAX_LIVES = 5;
const REVEAL_MS = 1250;

type Reveal = { optionId: number; correct: boolean | null } | null;

export default function GrammarPage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);
  useAudioUnlock();

  const [questions, setQuestions] = useState<GrammarQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [lives, setLives] = useState(MAX_LIVES);
  const [cleared, setCleared] = useState(0);
  const [reveal, setReveal] = useState<Reveal>(null);
  const [locked, setLocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [finished, setFinished] = useState<{
    success: boolean;
    percent: number;
    xp_awarded: number;
  } | null>(null);

  const answersRef = useRef<{ question_id: number; option_id: number }[]>([]);
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lockRef = useRef(false);
  const livesRef = useRef(MAX_LIVES);
  const clearedRef = useRef(0);
  const finishedRef = useRef(false);
  const indexRef = useRef(0);
  const questionsRef = useRef<GrammarQuestion[]>([]);
  const attemptIdRef = useRef<number | null>(null);

  useEffect(() => {
    indexRef.current = index;
  }, [index]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .startAttempt(missionId, "grammar")
      .then((res) => {
        const list = res.questions ?? [];
        if (list.length === 0) {
          setError("No grammar questions in this mission yet.");
          return;
        }
        setQuestions(list);
        questionsRef.current = list;
        attemptIdRef.current = res.attempt_id;
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [missionId, router]);

  const finishGame = useCallback(
    async () => {
      if (finishedRef.current) return;
      finishedRef.current = true;
      const id = attemptIdRef.current;
      if (!id) {
        setError("Attempt was not started.");
        return;
      }
      try {
        const res = await api.submitGrammar(missionId, id, answersRef.current);
        setFinished({
          success: res.passed,
          percent: res.percent,
          xp_awarded: res.xp_awarded,
        });
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [missionId],
  );

  const goNext = useCallback(() => {
    const next = indexRef.current + 1;
    if (next >= questionsRef.current.length || livesRef.current <= 0) {
      void finishGame();
      return;
    }
    setReveal(null);
    setLocked(false);
    lockRef.current = false;
    setIndex(next);
    indexRef.current = next;
  }, [finishGame]);

  const handlePick = useCallback(
    async (question: GrammarQuestion, optionId: number) => {
      if (locked || lockRef.current || finishedRef.current) return;
      lockRef.current = true;
      setLocked(true);
      setReveal({ optionId, correct: null });

      let correct = false;
      try {
        const res = await api.checkGrammar(missionId, question.id, optionId);
        correct = res.correct;
      } catch {
        // The server re-grades on submit; a failed live check is not fatal.
      }

      answersRef.current.push({ question_id: question.id, option_id: optionId });
      setReveal({ optionId, correct });

      if (correct) {
        const next = clearedRef.current + 1;
        clearedRef.current = next;
        setCleared(next);
      } else {
        const next = Math.max(0, livesRef.current - 1);
        livesRef.current = next;
        setLives(next);
      }

      if (advanceTimer.current) clearTimeout(advanceTimer.current);
      advanceTimer.current = setTimeout(() => {
        goNext();
      }, REVEAL_MS);
    },
    [goNext, locked, missionId],
  );

  useEffect(() => {
    return () => {
      if (advanceTimer.current) clearTimeout(advanceTimer.current);
    };
  }, []);

  if (loading) return <main className="page muted">Loading…</main>;

  if (error) {
    return (
      <main className="page accent">
        <p>{error}</p>
        <Link href={`/missions/${missionId}`} className="btn-eq-ghost mt-4">
          Back to lesson
        </Link>
      </main>
    );
  }

  if (finished) {
    return (
      <ResultScreen
        success={finished.success}
        percent={finished.percent}
        xpAwarded={finished.xp_awarded}
        onRetry={() => window.location.reload()}
        backHref={`/missions/${missionId}`}
      />
    );
  }

  const current = questions[index];
  if (!current) return <main className="page muted">No questions.</main>;

  return (
    <main className="page" style={{ maxWidth: 860 }}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/missions/${missionId}`} className="eq-back">
          <ArrowLeft size={16} /> Lesson
        </Link>
        <div className="flex items-center gap-2">
          <span className="eq-pill eq-pill--mint">
            <Trophy size={15} /> {cleared}/{questions.length}
          </span>
          <span className="eq-pill" aria-label={`Lives ${lives} of ${MAX_LIVES}`}>
            <span className="eq-hearts">
              {Array.from({ length: MAX_LIVES }).map((_, i) => (
                <Heart
                  key={i}
                  size={16}
                  className={i < lives ? "eq-heart" : "eq-heart--off"}
                  fill={i < lives ? "currentColor" : "none"}
                />
              ))}
            </span>
          </span>
        </div>
      </div>

      <div className="eq-grammar-stage">
        <div className="eq-grammar-stage__head">
          <span className="eq-quiz__badge">
            Question {index + 1} of {questions.length}
          </span>
          <h1 className="eq-grammar-q" key={`q-${current.id}`}>
            {current.question_text}
          </h1>
          <p className="eq-caption" style={{ margin: 0 }}>
            Tap the correct word form before it settles.
          </p>
        </div>

        <div className="eq-grammar-words" key={`w-${current.id}`}>
          {current.options.map((option, i) => {
            const picked = reveal?.optionId === option.id;
            const state =
              picked && reveal?.correct === null
                ? "picked"
                : picked
                  ? reveal?.correct
                    ? "correct"
                    : "wrong"
                  : "idle";
            return (
              <button
                key={option.id}
                type="button"
                className={`eq-grammar-word ${state}`}
                style={{ animationDelay: `${i * 40}ms` }}
                disabled={locked}
                onClick={() => handlePick(current, option.id)}
                aria-label={option.option_text}
              >
                <span>{option.option_text}</span>
                {picked && reveal?.correct !== null && (
                  <span className="eq-grammar-word__mark">
                    {reveal?.correct ? <Check size={18} /> : <X size={18} />}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="eq-grammar-status" aria-live="polite">
          {reveal && reveal.correct !== null && (
            <span className={reveal.correct ? "eq-grammar-ok" : "eq-grammar-bad"}>
              {reveal.correct ? "Correct!" : "Not quite — keep going"}
            </span>
          )}
        </div>
      </div>

      <p className="eq-caption mt-5" style={{ margin: 0, textAlign: "center" }}>
        Four forms of the same word fly in. Click the one that fits the sentence — no microphone
        needed.
      </p>
    </main>
  );
}
