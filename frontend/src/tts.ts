import { useEffect, useState } from "react";

import type { Lang } from "./api/client";

// Text to speech with the browser's own voices (speechSynthesis). Nothing is sent anywhere by the app.
// Which voices exist depends on the phone: many have English and Hindi, fewer have Marathi.

// Voices to try for each language, best first. Hinglish is Hindi written in Latin letters, which an
// Indian English voice reads far better than a Hindi voice does. Marathi falls back to Hindi:
// both use Devanagari, so a Hindi voice can read Marathi text.
export const VOICE_PREFS: Record<Lang, string[]> = {
  en: ["en-IN", "en-GB", "en-US", "en"],
  hi: ["hi-IN", "hi"],
  hinglish: ["en-IN", "hi-IN", "en"],
  mr: ["mr-IN", "mr", "hi-IN", "hi"],
};

export function ttsSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";
}

function norm(tag: string) {
  return tag.replace("_", "-").toLowerCase();
}

/** The best installed voice for a language, or null (the browser default is then used). */
export function pickVoice(voices: SpeechSynthesisVoice[], lang: Lang): SpeechSynthesisVoice | null {
  for (const want of VOICE_PREFS[lang]) {
    const w = norm(want);
    const exact = voices.find((v) => norm(v.lang) === w);
    if (exact) return exact;
    if (!w.includes("-")) {
      const prefix = voices.find((v) => norm(v.lang).startsWith(w + "-"));
      if (prefix) return prefix;
    }
  }
  return null;
}

/** Installed voices; they load asynchronously in Chrome, so this re-renders when they arrive. */
export function useVoices(): SpeechSynthesisVoice[] {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>(() => (ttsSupported() ? window.speechSynthesis.getVoices() : []));
  useEffect(() => {
    if (!ttsSupported()) return;
    const synth = window.speechSynthesis;
    const update = () => setVoices(synth.getVoices());
    update();
    synth.addEventListener?.("voiceschanged", update);
    return () => synth.removeEventListener?.("voiceschanged", update);
  }, []);
  return voices;
}

export function stopSpeaking() {
  if (ttsSupported()) window.speechSynthesis.cancel();
}

/** Speak the parts one after another. Resolves when all are spoken, or early if cancelled. */
export function speakAll(parts: { text: string; lang: Lang }[], voices: SpeechSynthesisVoice[], signal: { cancelled: boolean }): Promise<void> {
  if (!ttsSupported()) return Promise.resolve();
  const synth = window.speechSynthesis;
  return parts.reduce<Promise<void>>(
    (prev, part) =>
      prev.then(
        () =>
          new Promise<void>((resolve) => {
            if (signal.cancelled || !part.text.trim()) return resolve();
            const u = new SpeechSynthesisUtterance(part.text);
            const v = pickVoice(voices, part.lang);
            u.lang = v?.lang ?? VOICE_PREFS[part.lang][0];
            if (v) u.voice = v;
            u.rate = 0.95; // a little slower than normal: the listener is busy and stressed
            u.onend = () => resolve();
            u.onerror = () => resolve();
            synth.speak(u);
          }),
      ),
    Promise.resolve(),
  );
}
