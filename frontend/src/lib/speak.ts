/**
 * Browser text-to-speech via the Web Speech Synthesis API.
 * No files or API keys — the voice comes from the OS.
 */
export function speak(text: string, lang = "en-US") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    u.rate = 0.95;
    u.pitch = 1;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find((v) => v.lang === lang) ?? voices.find((v) => v.lang.startsWith("en"));
    if (preferred) u.voice = preferred;
    window.speechSynthesis.speak(u);
  } catch {
    /* ignore */
  }
}

export function speechAvailable() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
