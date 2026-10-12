"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Mic, Volume2 } from "lucide-react";

import { speak } from "@/lib/speak";
import { ResultScreen } from "@/components/result-screen";
import { useAudioUnlock } from "@/components/use-audio-unlock";
import { api, getToken, Mission, VocabularyItem } from "@/services/api";

export default function PronouncePage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);
  useAudioUnlock();

  const [mission, setMission] = useState<Mission | null>(null);
  const [items, setItems] = useState<VocabularyItem[]>([]);
  const [index, setIndex] = useState(0);
  const [status, setStatus] = useState<"idle" | "listening" | "correct" | "wrong">("idle");
  const [transcript, setTranscript] = useState("");
  const [speechSupported, setSpeechSupported] = useState(true);
  const [done, setDone] = useState(false);
  const [result, setResult] = useState<{ percent: number; passed: boolean } | null>(null);
  const [error, setError] = useState("");
  const [correctCount, setCorrectCount] = useState(0);
  const recognitionRef = useRef<any>(null);
  const correctRef = useRef(0);
  const answersRef = useRef<{ item_id: number; word: string }[]>([]);
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (typeof window !== "undefined") {
      const w = window as any;
      setSpeechSupported(Boolean(w.SpeechRecognition || w.webkitSpeechRecognition));
    }
    Promise.all([api.mission(missionId), api.missionVocabulary(missionId)])
      .then(([m, vocab]) => {
        setMission(m);
        if (vocab.length === 0) setError("No pronunciation items in this mission.");
        // 10 random words out of all available
        const shuffled = [...vocab].sort(() => Math.random() - 0.5);
        setItems(shuffled.slice(0, Math.min(10, shuffled.length)));
      })
      .catch((e) => setError(e.message));
  }, [missionId, router]);

  const normalizeTokens = (v: string): string[] => v.toLowerCase().match(/[a-z0-9]+/g) ?? [];

  const evaluate = useCallback((spoken: string, expected: string) => {
    const spokenTokens = normalizeTokens(spoken);
    const targetTokens = normalizeTokens(expected);
    if (spokenTokens.length === 0 || targetTokens.length === 0) return false;
    // Whole-token matching: "car" must not match "carpet".
    if (targetTokens.length === 1) return spokenTokens.includes(targetTokens[0]);
    return spokenTokens.join(" ").includes(targetTokens.join(" "));
  }, []);

  const completePronunciation = useCallback(
    async (answers: { item_id: number; word: string }[]) => {
      setDone(true);
      try {
        const res = await api.submitPronunciation(missionId, answers);
        setResult({ percent: res.percent, passed: res.passed });
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [missionId],
  );

  // Finalise a word result and move on — no retry, no text input.
  const resolveWord = useCallback(
    (spoken: string, expected: string, itemId: number) => {
      const correct = evaluate(spoken, expected);
      setStatus(correct ? "correct" : "wrong");
      answersRef.current.push({ item_id: itemId, word: spoken });
      if (correct) {
        correctRef.current += 1;
        setCorrectCount(correctRef.current);
      }
      if (advanceTimer.current) clearTimeout(advanceTimer.current);
      advanceTimer.current = setTimeout(() => {
        setStatus("idle");
        setTranscript("");
        setIndex((prev) => {
          const next = prev + 1;
          if (next >= items.length) {
            void completePronunciation(answersRef.current);
            return prev;
          }
          return next;
        });
      }, 1100);
    },
    [items.length, completePronunciation, evaluate],
  );

  const startListening = useCallback(
    (expected: string, itemId: number) => {
      const w = window as any;
      const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
      if (!Ctor) {
        setSpeechSupported(false);
        return;
      }
      const r = new Ctor();
      r.lang = "en-US";
      r.continuous = false;
      r.interimResults = true;
      let handled = false;
      r.onresult = (event: any) => {
        if (handled) return;
        const text = Array.from(event.results).map((x: any) => x[0].transcript).join(" ");
        setTranscript(text);
        if (event.results[event.results.length - 1].isFinal) {
          handled = true;
          resolveWord(text, expected, itemId);
        }
      };
      r.onerror = () => setStatus((p) => (p === "listening" ? "idle" : p));
      r.onend = () => setStatus((p) => (p === "listening" ? "idle" : p));
      recognitionRef.current = r;
      setTranscript("");
      setStatus("listening");
      try {
        r.start();
      } catch {
        setStatus("idle");
      }
    },
    [resolveWord],
  );

  function stopListening() {
    recognitionRef.current?.stop();
    setStatus("idle");
  }

  useEffect(() => {
    return () => {
      if (advanceTimer.current) clearTimeout(advanceTimer.current);
      recognitionRef.current?.abort?.();
    };
  }, []);

  if (error) return <main className="page accent">{error}</main>;
  if (!mission) return <main className="page muted">Loading…</main>;
  if (items.length === 0) return <main className="page muted">No items.</main>;

  if (done) {
    return (
      <ResultScreen
        success={Boolean(result?.passed)}
        percent={result?.percent ?? 0}
        onRetry={() => {
          setDone(false);
          setIndex(0);
          setStatus("idle");
          correctRef.current = 0;
          answersRef.current = [];
          setCorrectCount(0);
          setResult(null);
        }}
        backHref={`/missions/${missionId}`}
      />
    );
  }

  const current = items[index];
  const answered = status === "correct" || status === "wrong";

  return (
    <main className="page" style={{ maxWidth: 560 }}>
      <Link href={`/missions/${missionId}`} className="eq-back">
        <ArrowLeft size={16} /> Lesson
      </Link>

      <div className="mt-6 flex items-baseline justify-between">
        <h1 className="eq-h1">Pronunciation</h1>
        <span className="eq-caption">
          {index + 1} / {items.length}
        </span>
      </div>

      <div className="eq-card mt-6 flex flex-col items-center gap-4 py-10 text-center">
        {current.image_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={current.image_url} alt="" width={140} height={140} style={{ borderRadius: 16 }} />
        )}

        <div className="flex items-center gap-2">
          <span style={{ fontSize: 34, fontWeight: 500, letterSpacing: "-0.02em", lineHeight: 1.1 }}>
            {current.word_en}
          </span>
          <button
            className="muted"
            onClick={() => speak(current.word_en)}
            aria-label="Listen"
            title="Listen"
          >
            <Volume2 size={22} />
          </button>
        </div>
        {current.transcription && (
          <div className="eq-caption" style={{ marginTop: -6, fontSize: 15 }}>
            {current.transcription}
          </div>
        )}
        <div className="muted" style={{ fontSize: 15 }}>
          {current.word_ru}
        </div>

        {speechSupported ? (
          <button
            className={`eq-circle available ${status === "listening" ? "mic-active" : ""}`}
            style={{ width: 92, height: 92, marginTop: 6 }}
            onClick={() => (status === "listening" ? stopListening() : startListening(current.word_en, current.id))}
            disabled={answered}
            aria-label="Speak"
          >
            <Mic size={34} strokeWidth={1.75} />
          </button>
        ) : (
          <p className="eq-caption" style={{ margin: 0 }}>
            Speech recognition is unavailable in this browser. Please use Chrome, Edge or Safari.
          </p>
        )}

        {status === "listening" && <p className="eq-caption" style={{ margin: 0 }}>Listening… tap to stop</p>}
        {transcript && <p className="eq-caption" style={{ margin: 0 }}>You said: “{transcript}”</p>}
        {status === "correct" && (
          <p style={{ margin: 0, color: "var(--eq-accent)", fontWeight: 500 }}>Correct</p>
        )}
        {status === "wrong" && (
          <p style={{ margin: 0, fontWeight: 500 }}>Not quite — it&apos;s “{current.word_en}”. No point this time.</p>
        )}
      </div>

      {answered && (
        <p className="eq-caption mt-4" style={{ textAlign: "center" }}>
          {index + 1 >= items.length ? "Finishing…" : "Next word…"}
        </p>
      )}
    </main>
  );
}
