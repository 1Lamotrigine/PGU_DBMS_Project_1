"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type Props = {
  success: boolean;
  percent: number;
  xpAwarded?: number;
  threshold?: number;
  onRetry?: () => void;
  backHref: string;
  backLabel?: string;
};

/**
 * End-of-module result screen.
 * Success -> loop the win video (Booba). Failure -> play the lose video (cat + laugh).
 * Both videos already contain their own audio.
 */
export function ResultScreen({
  success,
  percent,
  xpAwarded,
  threshold = 70,
  onRetry,
  backHref,
  backLabel = "Back to lesson",
}: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [muted, setMuted] = useState(false);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = 0;
    // try with sound; if the browser blocks it, fall back to muted autoplay
    v.play().catch(() => {
      setMuted(true);
      v.muted = true;
      v.play().catch(() => {});
    });
  }, [success]);

  function toggleSound() {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
    v.play().catch(() => {});
  }

  return (
    <main className="page" style={{ maxWidth: 560 }}>
      <div className="result-media">
        <video
          ref={videoRef}
          src={success ? "/media/win.mp4" : "/media/lose.mp4"}
          autoPlay
          playsInline
          loop={success}
          muted={muted}
          controls={false}
        />
        <button className="result-sound" onClick={toggleSound} aria-label="Toggle sound">
          {muted ? "🔇" : "🔊"}
        </button>
      </div>

      <div style={{ textAlign: "center", marginTop: 20 }}>
        <h1 className="eq-h1">{success ? "Module passed" : "Not this time"}</h1>
        <p className="eq-sub">
          {percent}% · threshold {threshold}%
        </p>
        {typeof xpAwarded === "number" && (
          <p style={{ fontSize: 20, fontWeight: 500, marginTop: 12 }}>+{xpAwarded} XP</p>
        )}

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {!success && onRetry && (
            <button className="btn-eq" onClick={onRetry}>
              Try again
            </button>
          )}
          <Link href={backHref} className={`btn-eq${success && onRetry ? "" : "-ghost"}`}>
            {backLabel}
          </Link>
        </div>
      </div>
    </main>
  );
}
