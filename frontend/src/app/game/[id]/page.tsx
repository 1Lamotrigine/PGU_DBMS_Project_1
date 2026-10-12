"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Heart, Mic, Trophy } from "lucide-react";

import { LaneScene, LaneSceneHandle, Lane } from "@/components/word-scene";
import { ResultScreen } from "@/components/result-screen";
import { useAudioUnlock } from "@/components/use-audio-unlock";
import { useTheme } from "@/components/theme-provider";
import { api, getToken, VocabularyItem } from "@/services/api";

const MAX_LIVES = 5;
const WIN_WORDS = 10; // correct words needed to win
const SPAWN_START_MS = 3000;
const SPAWN_MIN_MS = 1900;

export default function GamePage() {
  const params = useParams();
  const router = useRouter();
  const missionId = Number(params.id);
  const { theme } = useTheme();
  useAudioUnlock();

  const sceneRef = useRef<LaneSceneHandle | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [vocab, setVocab] = useState<VocabularyItem[]>([]);
  const [lives, setLives] = useState(MAX_LIVES);
  const [cleared, setCleared] = useState(0);
  const [micOn, setMicOn] = useState(false);
  const [micError, setMicError] = useState("");
  const [heard, setHeard] = useState<string>("");
  const [lastResult, setLastResult] = useState<"hit" | "miss" | null>(null);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [finished, setFinished] = useState<
    { success: boolean; percent: number; xp_awarded: number } | null
  >(null);

  const finishedRef = useRef(false);
  const livesRef = useRef(MAX_LIVES);
  const clearedRef = useRef(0);
  const vocabRef = useRef<VocabularyItem[]>([]);
  const liveCardsRef = useRef<Map<number, Lane>>(new Map());
  const nextIdRef = useRef(1);
  const queueRef = useRef<VocabularyItem[]>([]);
  const recognitionRef = useRef<any>(null);
  const micStoppedRef = useRef(false);
  const attemptIdRef = useRef<number | null>(null);
  const answersRef = useRef<{ item_id: number; word: string }[]>([]);

  useEffect(() => {
    livesRef.current = lives;
    clearedRef.current = cleared;
    vocabRef.current = vocab;
  }, [lives, cleared, vocab]);

  const normalize = (v: string): string[] => v.toLowerCase().match(/[a-z0-9]+/g) ?? [];

  // ---- load ----
  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (typeof window !== "undefined") {
      const w = window as any;
      setSpeechSupported(Boolean(w.SpeechRecognition || w.webkitSpeechRecognition));
    }
    api
      .startAttempt(missionId, "game")
      .then((res) => {
        const v = res.items ?? [];
        if (v.length < 2) {
          setError("Not enough vocabulary for this mission yet.");
          return;
        }
        attemptIdRef.current = res.attempt_id;
        setVocab(v);
        vocabRef.current = v;
        // shuffled queue — every word appears exactly once
        queueRef.current = shuffle([...v]);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [missionId, router]);

  const finishGame = useCallback(
    async (finalCleared: number) => {
      if (finishedRef.current) return;
      finishedRef.current = true;
      micStoppedRef.current = true;
      stopMic();
      try {
        const res = await api.submitGame(missionId, attemptIdRef.current ?? 0, answersRef.current);
        setFinished({ success: res.success, percent: res.percent, xp_awarded: res.xp_awarded });
      } catch (e) {
        setError((e as Error).message);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [missionId],
  );

  const loseLife = useCallback(() => {
    setLastResult("miss");
    window.setTimeout(() => setLastResult(null), 350);
    const next = livesRef.current - 1;
    setLives(next);
    livesRef.current = next;
    if (next <= 0) void finishGame(clearedRef.current);
  }, [finishGame]);

  // if all words have spawned and none remain in play, end the round
  const maybeFinishWhenExhausted = useCallback(() => {
    if (finishedRef.current) return;
    if (queueRef.current.length === 0 && liveCardsRef.current.size === 0) {
      void finishGame(clearedRef.current);
    }
  }, [finishGame]);

  // ---- spawn loop ----
  useEffect(() => {
    if (loading || error || finished) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    function schedule() {
      if (queueRef.current.length === 0) return; // all words used
      const ratio = clearedRef.current / WIN_WORDS;
      const interval = SPAWN_START_MS - (SPAWN_START_MS - SPAWN_MIN_MS) * Math.min(ratio, 1);
      timer = setTimeout(() => {
        if (cancelled || finishedRef.current) return;
        spawnCard();
        schedule();
      }, interval);
    }

    function spawnCard() {
      const pick = queueRef.current.shift();
      if (!pick) return;
      const id = nextIdRef.current++;
      const lane: Lane = { id, itemId: pick.id, ru: pick.word_ru, en: pick.word_en, image: pick.image_url };
      liveCardsRef.current.set(id, lane);
      sceneRef.current?.addCard(lane);
    }

    schedule();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, error, finished]);

  const handleBreach = useCallback(
    (lane: Lane) => {
      liveCardsRef.current.delete(lane.id);
      loseLife();
      maybeFinishWhenExhausted();
    },
    [loseLife, maybeFinishWhenExhausted],
  );

  // ---- continuous microphone ----
  const handleSpokenRef = useRef<(text: string) => void>(() => {});
  const restartingRef = useRef(false);

  const startMic = useCallback(() => {
    const w = window as any;
    const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!Ctor) {
      setSpeechSupported(false);
      return;
    }
    if (recognitionRef.current) return; // already running
    // Always build a fresh instance — reusing a stopped one silently fails.
    const r = new Ctor();
    r.lang = "en-US";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 3;

    r.onstart = () => {
      setMicOn(true);
      setMicError("");
    };

    r.onresult = (event: any) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const text = res[0].transcript;
        if (res.isFinal) {
          setHeard(text.trim());
          handleSpokenRef.current(text);
        } else {
          interim += text;
        }
      }
      if (interim) {
        setHeard(interim);
        // also try matching interim speech so the game feels responsive
        handleSpokenRef.current(interim);
      }
    };

    r.onerror = (e: any) => {
      const err = e?.error ?? "unknown";
      setMicError(String(err));
      if (err === "not-allowed" || err === "service-not-allowed") {
        setMicOn(false);
        micStoppedRef.current = true;
      }
    };

    r.onend = () => {
      recognitionRef.current = null;
      setMicOn(false);
      // Auto-restart to keep the mic on for the whole game.
      if (!micStoppedRef.current && !finishedRef.current && !restartingRef.current) {
        restartingRef.current = true;
        window.setTimeout(() => {
          restartingRef.current = false;
          if (!micStoppedRef.current && !finishedRef.current) startMic();
        }, 300);
      }
    };

    recognitionRef.current = r;
    try {
      r.start();
    } catch {
      // start() can throw if called too soon; retry shortly.
      recognitionRef.current = null;
      if (!micStoppedRef.current && !finishedRef.current) {
        window.setTimeout(() => startMic(), 400);
      }
    }
  }, []);

  function stopMic() {
    const r = recognitionRef.current;
    if (!r) return;
    r.onend = null;
    try {
      r.stop();
    } catch {
      /* ignore */
    }
    recognitionRef.current = null;
    setMicOn(false);
  }

  const handleSpoken = useCallback(
    (spoken: string) => {
      if (finishedRef.current) return;
      const words = normalize(spoken);
      if (words.length === 0) return;

      // find a live card whose English translation was spoken (whole-token matching)
      let matched: { id: number; lane: Lane } | null = null;
      for (const [id, lane] of liveCardsRef.current.entries()) {
        const targetTokens = normalize(lane.en);
        if (targetTokens.length === 0) continue;
        const hit =
          targetTokens.length === 1
            ? words.includes(targetTokens[0])
            : words.join(" ").includes(targetTokens.join(" "));
        if (hit) {
          matched = { id, lane };
          break;
        }
      }

      if (matched) {
        liveCardsRef.current.delete(matched.id);
        // Record the spoken word against the issued vocabulary item for the server.
        if (matched.lane.itemId != null) {
          answersRef.current.push({ item_id: matched.lane.itemId, word: spoken });
        }
        sceneRef.current?.destroyCard(matched.id, true);
        setLastResult("hit");
        window.setTimeout(() => setLastResult(null), 350);
        const nextCleared = clearedRef.current + 1;
        setCleared(nextCleared);
        clearedRef.current = nextCleared;
        if (nextCleared >= WIN_WORDS) void finishGame(nextCleared);
      }
      maybeFinishWhenExhausted();
    },
    [finishGame, maybeFinishWhenExhausted],
  );

  // keep a stable ref to the latest handler for the recognition callback
  handleSpokenRef.current = handleSpoken;

  // start mic when ready
  useEffect(() => {
    if (!loading && !error && !finished && speechSupported) {
      startMic();
    }
    return () => {
      // keep mic across renders; stop only on unmount via separate effect
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, error, finished, speechSupported]);

  // watchdog: if recognition died silently, restart it
  useEffect(() => {
    if (loading || error || finished || !speechSupported) return;
    const id = setInterval(() => {
      if (!micStoppedRef.current && !finishedRef.current && !recognitionRef.current) {
        startMic();
      }
    }, 1500);
    return () => clearInterval(id);
  }, [loading, error, finished, speechSupported, startMic]);

  useEffect(() => {
    return () => {
      micStoppedRef.current = true;
      recognitionRef.current?.abort?.();
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

  const accent = theme === "dark" ? "#FFD23F" : "#130F3A";
  const bg = theme === "dark" ? "#130F3A" : "#F2F0FF";
  const textColor = theme === "dark" ? "#F4F3FF" : "#130F3A";
  const wallColor = theme === "dark" ? "#3B3680" : "#DDD8F7";

  return (
    <main className="page" style={{ maxWidth: 860 }}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/missions/${missionId}`} className="eq-back">
          <ArrowLeft size={16} /> Lesson
        </Link>
        <div className="flex items-center gap-2">
          <span className="eq-pill eq-pill--mint">
            <Trophy size={15} /> {cleared}/{WIN_WORDS}
          </span>
          <span className="eq-pill" aria-label={`Health ${Math.max(0, lives)} of ${MAX_LIVES}`}>
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

      {/* Battlefield */}
      <div
        className="relative overflow-hidden"
        style={{
          height: 460,
          border: `3px solid ${lastResult === "hit" ? "var(--eq-mint)" : lastResult === "miss" ? "var(--eq-coral)" : "var(--eq-border)"}`,
          borderRadius: 26,
          background: bg,
          transition: "border-color 0.2s ease",
          boxShadow: "var(--eq-shadow)",
        }}
      >
        <LaneScene
          ref={sceneRef}
          accent={accent}
          bg={bg}
          textColor={textColor}
          wallColor={wallColor}
          onBreach={handleBreach}
        />
      </div>

      {/* Voice status */}
      <div className="mt-5 flex flex-col items-center gap-3">
        <div className={`eq-mic ${micOn ? "eq-mic--on" : ""}`}>
          <span className={`eq-mic__icon ${micOn ? "mic-active" : ""}`}>
            <Mic size={20} strokeWidth={2} />
          </span>
          <span className="eq-caption" style={{ color: "inherit" }}>
            {!speechSupported
              ? "Microphone unavailable — use a Chromium-based browser"
              : micOn
                ? "Microphone on — say the English word"
                : micError
                  ? `Microphone error: ${micError}`
                  : "Starting microphone…"}
          </span>
        </div>
        {heard && <p className="eq-caption" style={{ margin: 0 }}>Heard: “{heard}”</p>}
      </div>

      <p className="eq-caption mt-5" style={{ margin: 0, textAlign: "center" }}>
        Pictures fly toward your base. Say the English word for each one out loud before it reaches
        the left edge — every breach costs 1 heart.
      </p>
    </main>
  );
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
