import { useCallback, useEffect, useRef, useState } from "react";

import { api, type Lang } from "./api/client";

// Browser speech recognition (Web Speech API). Chrome and Safari support it; Firefox does not,
// so callers hide the mic when `supported` is false. The transcript is only ever placed in the
// text box: the user reads it and presses Continue, nothing is submitted automatically.
//
// The browser recogniser must be told the language before it starts, and cannot detect it. So the
// mic starts in a best guess and, once it has heard a few words, asks the trained language model
// (/api/langid) what was said. If that is a different language with confidence, it restarts the
// recogniser in that language, keeping the text heard so far. The user never has to pick a language.

// Hinglish uses Hindi recognition: it handles Hindi mixed with English words.
export const SPEECH_LANG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", hinglish: "hi-IN", mr: "mr-IN" };

export const SWITCH_CONFIDENCE = 0.85; // the language model must be at least this sure before the mic switches
const MAX_SWITCHES = 2; // per listening session, so it can never flip back and forth for long
const MIN_WORDS = 3;

export type SpeechError = "denied" | "no_speech" | "failed";
export type Detect = (text: string) => Promise<{ lang: Lang; p?: number }>;

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

/** Where to start listening when nobody has said which language they speak.
 *  Hindi recognition is the best hub: Hindi and Hinglish come out right, English words usually stay
 *  in Latin letters, and Marathi comes out in Devanagari, so the language model can tell all four apart. */
export function initialSpeechLang(preferred: Lang | null): Lang {
  if (preferred) return preferred;
  const prefs = typeof navigator !== "undefined" ? navigator.languages ?? [navigator.language] : [];
  if (prefs.some((l) => l?.toLowerCase().startsWith("mr"))) return "mr";
  return "hi";
}

const words = (s: string) => s.trim().split(/\s+/).filter(Boolean).length;

/** `onText` receives the full transcript so far for this listening session.
 *  `preferred` is the language the user picked, or null if they have not picked one. */
export function useSpeechInput(preferred: Lang | null, onText: (transcript: string) => void, detect: Detect = api.langid) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<SpeechError | null>(null);
  const [heard, setHeard] = useState<Lang | null>(null); // language the mic switched to, for the status line
  const rec = useRef<Recognition | null>(null);
  const session = useRef({ prefix: "", switches: 0, lang: "hi" as Lang, next: null as Lang | null, checking: false, checkedAt: 0 });
  const onTextRef = useRef(onText);
  onTextRef.current = onText;
  const detectRef = useRef(detect);
  detectRef.current = detect;

  const stop = useCallback(() => {
    session.current.next = null;
    rec.current?.stop();
  }, []);

  const begin = useCallback((lang: Lang) => {
    const Cls = recognitionClass();
    if (!Cls) return;
    const s = session.current;
    s.lang = lang;
    s.checkedAt = 0;
    const r = new Cls();
    r.lang = SPEECH_LANG[lang];
    r.interimResults = true;
    r.continuous = true;
    r.maxAlternatives = 1;
    r.onresult = (e) => {
      let transcript = "";
      let final = false;
      for (let i = 0; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
        final = final || e.results[i].isFinal;
      }
      transcript = transcript.trim();
      onTextRef.current([s.prefix, transcript].filter(Boolean).join(" "));
      // Check the language once a few words are in, and again after each finished phrase.
      const n = words(transcript);
      if (s.checking || s.switches >= MAX_SWITCHES || n < MIN_WORDS || (n === s.checkedAt && !final)) return;
      s.checking = true;
      s.checkedAt = n;
      detectRef
        .current(transcript)
        .then(({ lang: found, p }) => {
          if (rec.current !== r || (p ?? 0.9) < SWITCH_CONFIDENCE) return;
          if (SPEECH_LANG[found] === SPEECH_LANG[s.lang]) return;
          s.prefix = [s.prefix, transcript].filter(Boolean).join(" ");
          s.next = found;
          setHeard(found);
          r.stop(); // onend restarts in the new language
        })
        .catch(() => undefined) // no network: keep listening in the current language
        .finally(() => {
          s.checking = false;
        });
    };
    r.onerror = (e) => {
      if (e.error === "aborted") return;
      setError(e.error === "not-allowed" || e.error === "service-not-allowed" ? "denied" : e.error === "no-speech" ? "no_speech" : "failed");
    };
    r.onend = () => {
      if (rec.current !== r) return;
      rec.current = null;
      const next = s.next;
      s.next = null;
      if (next) {
        s.switches += 1;
        begin(next);
        return;
      }
      setListening(false);
    };
    rec.current = r;
    try {
      r.start();
      setListening(true);
    } catch {
      rec.current = null;
      setListening(false);
      setError("failed");
    }
  }, []);

  const start = useCallback(() => {
    if (!recognitionClass() || rec.current) return;
    session.current = { prefix: "", switches: 0, lang: "hi", next: null, checking: false, checkedAt: 0 };
    setError(null);
    setHeard(null);
    begin(initialSpeechLang(preferred));
  }, [begin, preferred]);

  // Stop listening if the chosen language changes or the screen goes away.
  useEffect(
    () => () => {
      session.current.next = null;
      const r = rec.current;
      rec.current = null;
      r?.abort();
    },
    [preferred],
  );

  return { supported: speechSupported(), listening, error, heard, start, stop };
}
