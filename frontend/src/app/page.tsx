"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { BookOpen, Mic, Sparkles, TrendingUp } from "lucide-react";

import { getToken } from "@/services/api";

const BUBBLES = [
  { text: "Hello!", c: "var(--eq-sun)", x: "6%", y: "6%", r: "-4deg", d: "0.1s" },
  { text: "Привет!", c: "var(--eq-mint)", x: "78%", y: "10%", r: "5deg", d: "0.25s" },
  { text: "¡Hola!", c: "var(--eq-coral)", x: "68%", y: "78%", r: "-6deg", d: "0.4s" },
  { text: "Bonjour", c: "var(--eq-sky)", x: "4%", y: "74%", r: "4deg", d: "0.55s" },
  { text: "你好", c: "var(--eq-sun)", x: "88%", y: "46%", r: "-5deg", d: "0.7s" },
  { text: "Ciao!", c: "var(--eq-mint)", x: "38%", y: "4%", r: "6deg", d: "0.85s" },
];

const FEATURES = [
  {
    icon: Sparkles,
    variant: "eq-feat--sun",
    title: "Placement test",
    text: "Find your CEFR level from A0 to C2 in a few minutes.",
  },
  {
    icon: TrendingUp,
    variant: "eq-feat--sky",
    title: "Levels & missions",
    text: "Five focused missions per level, in a clear progression.",
  },
  {
    icon: Mic,
    variant: "eq-feat--mint",
    title: "Speak to score",
    text: "Say words out loud and get instant feedback.",
  },
  {
    icon: BookOpen,
    variant: "eq-feat--coral",
    title: "Picture dictionary",
    text: "Catch falling pictures and name them before they reach the base.",
  },
];

const STEPS = [
  { n: 1, title: "Take the placement test", text: "A few quick questions set your starting CEFR level." },
  { n: 2, title: "Clear the missions", text: "Test → pronunciation → dictionary game, in order." },
  { n: 3, title: "Speak out loud", text: "The microphone listens and scores every word you say." },
  { n: 4, title: "Collect XP", text: "Earn more XP the first time, a little on every repeat." },
];

const MARQUEE = ["English", "Español", "Deutsch", "Français", "中文", "Italiano", "日本語", "Қазақша", "한국어"];

export default function HomePage() {
  const [authed, setAuthed] = useState(false);
  const bubblesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  // Gentle parallax on the bubbles, echoing the index.html hero.
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const layer = bubblesRef.current;
    if (!layer) return;
    const onMove = (e: PointerEvent) => {
      const x = e.clientX / window.innerWidth - 0.5;
      const y = e.clientY / window.innerHeight - 0.5;
      layer.style.transform = `translate(${x * -18}px, ${y * -14}px)`;
    };
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <main className="page" style={{ paddingTop: 40 }}>
      {/* Hero */}
      <section
        className="eq-band eq-band--soft"
        style={{ position: "relative", borderRadius: 32, overflow: "hidden", paddingBlock: 64 }}
      >
        <div ref={bubblesRef} className="eq-bubbles" aria-hidden style={{ transition: "transform .3s ease-out" }}>
          {BUBBLES.map((b) => (
            <span
              key={b.text}
              className="eq-bub"
              style={{ ["--c" as string]: b.c, ["--x" as string]: b.x, ["--y" as string]: b.y, ["--r" as string]: b.r, ["--d" as string]: b.d }}
            >
              {b.text}
            </span>
          ))}
        </div>

        <div className="relative" style={{ maxWidth: 600, marginInline: "auto", textAlign: "center", zIndex: 1 }}>
          <span
            className="eq-label"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              background: "var(--eq-bg)",
              color: "var(--eq-text)",
              padding: "7px 16px",
              borderRadius: 999,
              marginBottom: 22,
            }}
          >
            Gamified English · A0 – C2
          </span>

          <h1 className="eq-h1" style={{ fontSize: "clamp(38px, 7vw, 60px)" }}>
            Learn English by speaking it
          </h1>
          <p className="eq-sub" style={{ fontSize: 19, marginInline: "auto" }}>
            A placement test, CEFR levels and short spoken missions. Speak words out loud, clear
            the falling pictures, and collect XP.
          </p>

          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <Link href={authed ? "/dashboard" : "/register"} className="btn-eq">
              {authed ? "Go to dashboard" : "Get started"}
            </Link>
            {!authed && (
              <Link href="/login" className="btn-eq-ghost">
                Log in
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Marquee */}
      <div className="eq-mq" aria-hidden>
        <div className="eq-mq__track">
          {[...MARQUEE, ...MARQUEE].map((w, i) => (
            <span key={i}>{w}</span>
          ))}
        </div>
      </div>

      {/* Feature cards */}
      <section style={{ paddingBlock: 56 }}>
        <h2 className="eq-h1" style={{ fontSize: "clamp(28px, 4vw, 40px)", textAlign: "center" }}>
          Everything you need, in one place
        </h2>
        <div className="mx-auto mt-10 grid gap-5 sm:grid-cols-2" style={{ maxWidth: 840 }}>
          {FEATURES.map(({ icon: Icon, variant, title, text }) => (
            <article key={title} className={`eq-feat ${variant}`}>
              <span className="eq-feat__ic">
                <Icon size={26} />
              </span>
              <h3 className="mt-4" style={{ fontSize: 22, fontWeight: 800 }}>
                {title}
              </h3>
              <p style={{ marginTop: 8, fontWeight: 500, opacity: 0.85 }}>{text}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Steps band */}
      <section className="eq-band eq-band--sun" style={{ borderRadius: 32 }}>
        <h2 className="eq-h1" style={{ fontSize: "clamp(28px, 4vw, 40px)", marginBottom: 36 }}>
          How a lesson flows
        </h2>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.n} className="eq-step">
              <span className="eq-step__num">{s.n}</span>
              <h3 style={{ fontSize: 19, fontWeight: 800 }}>{s.title}</h3>
              <p style={{ marginTop: 6, fontSize: 14, color: "var(--eq-muted)" }}>{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section style={{ textAlign: "center", paddingBlock: 72 }}>
        <h2 className="eq-h1" style={{ fontSize: "clamp(30px, 5vw, 46px)" }}>
          Ready to speak your first words?
        </h2>
        <p className="eq-sub" style={{ marginInline: "auto" }}>
          Create a free account and take the placement test in under five minutes.
        </p>
        <div className="mt-8 flex justify-center">
          <Link href={authed ? "/dashboard" : "/register"} className="btn-eq" style={{ fontSize: 17, minHeight: 52, padding: "0 32px" }}>
            {authed ? "Continue learning" : "Get started free"}
          </Link>
        </div>
      </section>
    </main>
  );
}
