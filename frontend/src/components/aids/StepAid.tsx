import { Check, Clock, Pause, Play, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { AidPhase, StepAid as Aid } from "../../api/client";
import {
  elapsed,
  formatClockTime,
  formatDuration,
  getClock,
  getCounter,
  getNotedTime,
  noteTime,
  pauseClock,
  resetClock,
  setCounter,
  startClock,
  subscribe,
} from "./store";

// Re-render whenever the aid store changes (start, pause, tap, note).
function useStore<T>(read: () => T): T {
  const [, force] = useState(0);
  useEffect(() => subscribe(() => force((n) => n + 1)), []);
  return read();
}

// Tick a few times a second while something is running.
function useNow(running: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    setNow(Date.now());
    const id = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(id);
  }, [running]);
  return now;
}

function buzz(ms = 30) {
  try {
    navigator.vibrate?.(ms);
  } catch {
    /* not supported */
  }
}

const card = "flex flex-col items-center gap-3 rounded-card border border-border bg-surface p-4";
const pill =
  "inline-flex min-h-[48px] items-center justify-center gap-2 rounded-full border border-border px-4 text-body font-semibold text-primary focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40";
const pillSolid =
  "inline-flex min-h-[48px] items-center justify-center gap-2 rounded-full bg-primary px-5 text-body font-semibold text-surface focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40";

function Ring({ fraction, children }: { fraction: number; children: React.ReactNode }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative flex h-36 w-36 items-center justify-center">
      <svg viewBox="0 0 120 120" className="absolute inset-0 h-full w-full -rotate-90" aria-hidden>
        <circle cx="60" cy="60" r={r} fill="none" strokeWidth="8" className="stroke-primary-soft" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className="stroke-primary"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - Math.min(1, Math.max(0, fraction)))}
        />
      </svg>
      <div className="relative flex flex-col items-center">{children}</div>
    </div>
  );
}

// Countdown for a duration the step states ("for at least 20 minutes", "up to 10 seconds").
export function TimerAid({ id, seconds }: { id: string; seconds: number }) {
  const { t } = useTranslation();
  const clock = useStore(() => getClock(id));
  const running = clock.startedAt !== null;
  const now = useNow(running);
  const total = seconds * 1000;
  const left = Math.max(0, total - elapsed(clock, now));
  const done = left === 0;

  useEffect(() => {
    if (done && running) {
      pauseClock(id);
      buzz(300);
    }
  }, [done, running, id]);

  const fresh = !running && clock.elapsedBefore === 0;
  return (
    <div className={card} data-testid="aid-timer">
      <Ring fraction={done ? 1 : 1 - left / total}>
        {done ? (
          <Check aria-hidden size={40} className="text-success" />
        ) : (
          <span className="text-step font-semibold tabular-nums text-text">{formatDuration(left)}</span>
        )}
        <span className="text-note text-text-muted">{done ? t("aid_done_short") : t("aid_left")}</span>
      </Ring>
      <p className="text-center text-body text-text" aria-live="polite">
        {done ? t("aid_timer_done") : running ? t(seconds <= 60 ? "aid_timer_running_short" : "aid_timer_running") : t("aid_timer_hint", { time: formatDuration(total) })}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {!done && (
          <button type="button" className={running ? pill : pillSolid} onClick={() => (running ? pauseClock(id) : startClock(id))}>
            {running ? <Pause aria-hidden size={18} /> : <Play aria-hidden size={18} />}
            {running ? t("aid_pause") : fresh ? t("aid_start") : t("aid_resume")}
          </button>
        )}
        {!fresh && (
          <button type="button" className={pill} onClick={() => resetClock(id)}>
            <RotateCcw aria-hidden size={18} />
            {t("aid_reset")}
          </button>
        )}
      </div>
    </div>
  );
}

// Counts up for steps that say "keep going until help arrives".
export function StopwatchAid({ id }: { id: string }) {
  const { t } = useTranslation();
  const clock = useStore(() => getClock(id));
  const running = clock.startedAt !== null;
  const now = useNow(running);
  const ms = Math.floor(elapsed(clock, now) / 1000) * 1000;
  const fresh = !running && clock.elapsedBefore === 0;
  return (
    <div className={card} data-testid="aid-stopwatch">
      <Ring fraction={(ms % 60000) / 60000}>
        <span className="text-step font-semibold tabular-nums text-text">{formatDuration(ms)}</span>
        <span className="text-note text-text-muted">{t("aid_elapsed")}</span>
      </Ring>
      <p className="text-center text-body text-text">{t("aid_stopwatch_hint")}</p>
      <div className="flex flex-wrap justify-center gap-2">
        <button type="button" className={running ? pill : pillSolid} onClick={() => (running ? pauseClock(id) : startClock(id))}>
          {running ? <Pause aria-hidden size={18} /> : <Play aria-hidden size={18} />}
          {running ? t("aid_pause") : fresh ? t("aid_start") : t("aid_resume")}
        </button>
        {!fresh && (
          <button type="button" className={pill} onClick={() => resetClock(id)}>
            <RotateCcw aria-hidden size={18} />
            {t("aid_reset")}
          </button>
        )}
      </div>
    </div>
  );
}

// "5 back blows, then 5 abdominal thrusts, repeat": tap once after each one.
export function CycleAid({ id, phases }: { id: string; phases: AidPhase[] }) {
  const { t } = useTranslation();
  const c = useStore(() => getCounter(id));
  const phase = phases[c.phase] ?? phases[0];
  const name = t(`aid_phase_${phase.key}`);

  const tap = () => {
    buzz();
    const done = c.done + 1;
    if (done < phase.count) setCounter(id, { ...c, done });
    else if (c.phase + 1 < phases.length) setCounter(id, { ...c, phase: c.phase + 1, done: 0 });
    else setCounter(id, { phase: 0, done: 0, round: c.round + 1 });
  };

  return (
    <div className={card} data-testid="aid-cycle">
      <div className="flex w-full items-center justify-between text-note text-text-muted">
        <span>{t("aid_round", { n: c.round })}</span>
        <span>
          {phases.map((p, i) => (
            <span key={p.key} className={i === c.phase ? "font-semibold text-primary" : ""}>
              {i > 0 ? " → " : ""}
              {p.count} × {t(`aid_phase_${p.key}`)}
            </span>
          ))}
        </span>
      </div>
      {phase.image ? (
        <img src={phase.image} alt="" className="h-40 w-full rounded-card border border-border bg-white object-contain" />
      ) : null}
      <p className="text-question font-semibold text-text" aria-live="polite">
        {name}: {c.done} / {phase.count}
      </p>
      <div className="flex gap-2" aria-hidden>
        {Array.from({ length: phase.count }, (_, i) => (
          <span key={i} className={`h-4 w-4 rounded-full ${i < c.done ? "bg-primary" : "border-2 border-primary bg-surface"}`} />
        ))}
      </div>
      <button type="button" className={`${pillSolid} w-full`} onClick={tap}>
        {t(`aid_tap_${phase.key}`)}
      </button>
      {(c.done > 0 || c.phase > 0 || c.round > 1) && (
        <button type="button" className={pill} onClick={() => setCounter(id, { phase: 0, done: 0, round: 1 })}>
          <RotateCcw aria-hidden size={18} />
          {t("aid_reset")}
        </button>
      )}
      <p className="text-center text-note text-text-muted">{t("aid_cycle_hint")}</p>
    </div>
  );
}

// "Note the time of the bite": one tap stores it, and it goes into the handover summary.
export function NoteTimeAid({ noteKey }: { noteKey: string }) {
  const { t, i18n } = useTranslation();
  const at = useStore(() => getNotedTime(noteKey));
  const [editing, setEditing] = useState(false);
  const toInput = (ms: number) => {
    const d = new Date(ms);
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  };
  return (
    <div className={card} data-testid="aid-note-time">
      <Clock aria-hidden size={32} className="text-primary" />
      {at === null ? (
        <>
          <p className="text-center text-body text-text">{t(`aid_note_${noteKey}_hint`)}</p>
          <button type="button" className={`${pillSolid} w-full`} onClick={() => (buzz(), noteTime(noteKey, Date.now()))}>
            {t(`aid_note_${noteKey}_now`)}
          </button>
          <button type="button" className={pill} onClick={() => (noteTime(noteKey, Date.now()), setEditing(true))}>
            {t("aid_note_earlier")}
          </button>
        </>
      ) : (
        <>
          <p className="text-center text-question font-semibold text-text" aria-live="polite">
            {t(`aid_note_${noteKey}_saved`, { time: formatClockTime(at, i18n.language) })}
          </p>
          {editing ? (
            <label className="flex flex-col items-center gap-2 text-body text-text">
              {t("aid_note_pick")}
              <input
                type="time"
                value={toInput(at)}
                onChange={(e) => {
                  const [h, m] = e.target.value.split(":").map(Number);
                  if (Number.isNaN(h) || Number.isNaN(m)) return;
                  const d = new Date();
                  d.setHours(h, m, 0, 0);
                  if (d.getTime() > Date.now()) d.setDate(d.getDate() - 1); // a later clock time means yesterday
                  noteTime(noteKey, d.getTime());
                }}
                className="min-h-[48px] rounded-card border border-border bg-surface px-3 text-body text-text focus:border-primary focus:outline-none"
              />
            </label>
          ) : (
            <button type="button" className={pill} onClick={() => setEditing(true)}>
              {t("aid_note_change")}
            </button>
          )}
          <p className="text-center text-note text-text-muted">{t("aid_note_in_summary")}</p>
        </>
      )}
    </div>
  );
}

export function StepAid({ stepId, aid }: { stepId: string; aid: Aid }) {
  switch (aid.kind) {
    case "timer":
      return <TimerAid id={stepId} seconds={aid.seconds} />;
    case "stopwatch":
      return <StopwatchAid id={stepId} />;
    case "cycle":
      return <CycleAid id={stepId} phases={aid.phases} />;
    case "note_time":
      return <NoteTimeAid noteKey={aid.key} />;
    default:
      return null;
  }
}
