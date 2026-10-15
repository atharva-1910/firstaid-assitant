import { Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { CPR_BPM } from "../theme/tokens";

function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined" && window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)").matches : false,
  );
  useEffect(() => {
    if (!window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const fn = () => setReduced(mq.matches);
    mq.addEventListener?.("change", fn);
    return () => mq.removeEventListener?.("change", fn);
  }, []);
  return reduced;
}

// A calm circle that grows and shrinks at 110 beats per minute (Section 14.6).
export function CprRhythm() {
  const { t } = useTranslation();
  const reduced = useReducedMotion();
  const [sound, setSound] = useState(false);
  const ctx = useRef<AudioContext | null>(null);
  const period = 60 / CPR_BPM;

  useEffect(() => {
    if (!sound) return;
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    ctx.current = ctx.current ?? new AC();
    const id = window.setInterval(() => {
      const c = ctx.current!;
      const osc = c.createOscillator();
      const gain = c.createGain();
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.04, c.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + 0.05);
      osc.connect(gain).connect(c.destination);
      osc.start();
      osc.stop(c.currentTime + 0.06);
    }, period * 1000);
    return () => window.clearInterval(id);
  }, [sound, period]);

  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-border bg-surface p-4">
      {reduced ? (
        <p className="text-body font-semibold text-text">{t("cpr_reduced_motion")}</p>
      ) : (
        <>
          <div className="flex h-28 w-28 items-center justify-center" aria-hidden>
            <div className="cpr-circle h-20 w-20 rounded-full bg-primary/80" style={{ animationDuration: `${period}s` }} />
          </div>
          <p className="text-note text-text-muted">{t("cpr_hint")}</p>
        </>
      )}
      <button
        type="button"
        onClick={() => setSound((s) => !s)}
        aria-pressed={sound}
        className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-border px-3 text-note text-primary"
      >
        {sound ? <Volume2 size={16} aria-hidden /> : <VolumeX size={16} aria-hidden />}
        {t("cpr_sound")}
      </button>
    </div>
  );
}
