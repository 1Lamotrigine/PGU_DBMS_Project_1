"use client";

import { useEffect, useRef } from "react";

/**
 * Browsers block autoplay-with-sound until the user interacts with the page.
 * This hook unlocks media playback on the first interaction so result videos
 * can play with sound afterwards.
 */
export function useAudioUnlock() {
  const unlockedRef = useRef(false);

  useEffect(() => {
    function unlock() {
      if (unlockedRef.current) return;
      unlockedRef.current = true;
      try {
        const audio = new Audio();
        audio.muted = true;
        const p = audio.play();
        if (p && typeof p.then === "function") p.then(() => audio.pause()).catch(() => {});
        // prime a video element too
        const v = document.createElement("video");
        v.muted = true;
        const vp = v.play();
        if (vp && typeof vp.then === "function") vp.then(() => v.pause()).catch(() => {});
      } catch {
        /* ignore */
      }
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    }
    window.addEventListener("pointerdown", unlock);
    window.addEventListener("keydown", unlock);
    window.addEventListener("touchstart", unlock);
    return () => {
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    };
  }, []);
}

export function isAudioUnlocked() {
  return typeof window !== "undefined" && (window as any).__eqAudioUnlocked === true;
}
