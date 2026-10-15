import { useCallback, useEffect, useRef, useState } from "react";

import type { Lang } from "./api/client";

// Browser speech recognition (Web Speech API). Chrome and Safari support it; Firefox does not,
// so callers hide the mic when `supported` is false. The transcript is only ever placed in the
// text box: the user reads it and presses Continue, nothing is submitted automatically.

// Hinglish uses Hindi recognition: it returns Devanagari, which the pipeline reads as Hindi.
export const SPEECH_LANG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", hinglish: "hi-IN", mr: "mr-IN" };

export type SpeechError = "denied" | "no_speech" | "failed";

type Recognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  onresult: ((e: { resultIndex: number; results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

function recognitionClass(): (new () => Recognition) | undefined {
  if (typeof window === "undefined") return undefined;
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

export function speechSupported(): boolean {
  return recognitionClass() !== undefined;
}

/** `onText` receives the full transcript so far (interim and final) for this listening session. */
export function useSpeechInput(lang: Lang, onText: (transcript: string) => void) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<SpeechError | null>(null);
  const rec = useRef<Recognition | null>(null);
  const onTextRef = useRef(onText);
  onTextRef.current = onText;

  const stop = useCallback(() => rec.current?.stop(), []);

  const start = useCallback(() => {
    const Cls = recognitionClass();
    if (!Cls || rec.current) return;
    const r = new Cls();
    r.lang = SPEECH_LANG[lang];
    r.interimResults = true;
    r.continuous = true;
    r.maxAlternatives = 1;
    r.onresult = (e) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript;
      onTextRef.current(transcript.trim());
    };
    r.onerror = (e) => {
      if (e.error === "aborted") return;
      setError(e.error === "not-allowed" || e.error === "service-not-allowed" ? "denied" : e.error === "no-speech" ? "no_speech" : "failed");
    };
    r.onend = () => {
      rec.current = null;
      setListening(false);
    };
    setError(null);
    rec.current = r;
    try {
      r.start();
      setListening(true);
    } catch {
      rec.current = null;
      setError("failed");
    }
  }, [lang]);

  // Stop listening if the language changes or the screen goes away.
  useEffect(() => () => rec.current?.abort(), [lang]);

  return { supported: speechSupported(), listening, error, start, stop };
}
