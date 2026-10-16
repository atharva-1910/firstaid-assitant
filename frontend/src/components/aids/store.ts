// Aid state lives outside React so a running timer keeps counting while the user moves
// between steps, and comes back showing the right time. Everything is cleared on "Start over".

export interface ClockState {
  startedAt: number | null; // when it last started running (ms), null while paused
  elapsedBefore: number; // ms counted before the last start
}

const clocks = new Map<string, ClockState>();
const counters = new Map<string, { phase: number; done: number; round: number }>();
const notedTimes = new Map<string, number>();
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

export function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function getClock(id: string): ClockState {
  return clocks.get(id) ?? { startedAt: null, elapsedBefore: 0 };
}

export function elapsed(c: ClockState, now: number): number {
  return c.elapsedBefore + (c.startedAt === null ? 0 : now - c.startedAt);
}

export function startClock(id: string, now = Date.now()) {
  const c = getClock(id);
  if (c.startedAt === null) clocks.set(id, { ...c, startedAt: now });
  emit();
}

export function pauseClock(id: string, now = Date.now()) {
  const c = getClock(id);
  if (c.startedAt !== null) clocks.set(id, { startedAt: null, elapsedBefore: elapsed(c, now) });
  emit();
}

export function resetClock(id: string) {
  clocks.delete(id);
  emit();
}

export function getCounter(id: string) {
  return counters.get(id) ?? { phase: 0, done: 0, round: 1 };
}

export function setCounter(id: string, v: { phase: number; done: number; round: number }) {
  counters.set(id, v);
  emit();
}

export function noteTime(key: string, at: number | null) {
  if (at === null) notedTimes.delete(key);
  else notedTimes.set(key, at);
  emit();
}

export function getNotedTime(key: string): number | null {
  return notedTimes.get(key) ?? null;
}

export function allNotedTimes(): [string, number][] {
  return [...notedTimes.entries()];
}

export function clearAids() {
  clocks.clear();
  counters.clear();
  notedTimes.clear();
  emit();
}

const LOCALE: Record<string, string> = { en: "en-IN", hinglish: "en-IN", hi: "hi-IN", mr: "mr-IN" };

export function formatClockTime(at: number, lang: string): string {
  return new Date(at).toLocaleTimeString(LOCALE[lang] ?? "en-IN", { hour: "numeric", minute: "2-digit" });
}

export function formatDuration(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
