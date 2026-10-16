import { act, fireEvent, render, screen } from "@testing-library/react";

import type { Step as S } from "../api/client";
import i18n from "../i18n";
import { AUTO_NEXT_MS, Step } from "../screens/Step";
import { pickVoice } from "../tts";

type Utt = { text: string; lang: string; voice: unknown; rate: number; onend: (() => void) | null; onerror: (() => void) | null };
const spoken: Utt[] = [];
const voices = [
  { lang: "en-IN", name: "English India" },
  { lang: "hi-IN", name: "Hindi" },
] as unknown as SpeechSynthesisVoice[];

class FakeUtterance {
  lang = "";
  voice: unknown = null;
  rate = 1;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public text: string) {}
}

const synth = {
  speak: (u: Utt) => spoken.push(u),
  cancel: vi.fn(),
  getVoices: () => voices,
  addEventListener: () => undefined,
  removeEventListener: () => undefined,
};

const base: S = {
  id: "ha_s1", order: 1, text: "Call 112 now.", translation_pending: false, rephrased: false,
  source: { doc: "G1", page: 358 }, also_in: [], agreement: "unchecked", evidence: "unchecked", verified: false,
  cpr_rhythm: false, link: null, do_not: [{ text: "Do not wait to see if the pain passes.", reason: "", translation_pending: false }],
};
const steps: S[] = [base, { ...base, id: "ha_s2", order: 2, text: "Help them sit.", do_not: [] }];

function finishSpeaking() {
  // Finish each utterance in turn (the next one is queued only after the previous ends).
  for (let i = 0; i < 10; i++) {
    const u = spoken.find((x) => !(x as unknown as { done?: boolean }).done);
    if (!u) break;
    (u as unknown as { done: boolean }).done = true;
    u.onend?.();
  }
}

async function speakThrough() {
  await act(async () => {
    for (let i = 0; i < 20; i++) {
      finishSpeaking();
      await Promise.resolve();
    }
  });
}

beforeEach(() => {
  spoken.length = 0;
  vi.useFakeTimers();
  vi.stubGlobal("speechSynthesis", synth);
  vi.stubGlobal("SpeechSynthesisUtterance", FakeUtterance);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  act(() => void i18n.changeLanguage("en"));
});

describe("read steps aloud", () => {
  it("is off until the user turns it on", () => {
    render(<Step steps={steps} index={0} urgency="emergency" onNext={() => {}} onBack={() => {}} onLink={() => {}} onMoreInfo={() => {}} busy={false} onToggleRead={() => {}} />);
    expect(spoken).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Read steps aloud" }).getAttribute("aria-pressed")).toBe("false");
  });

  it("reads the step and its warning, then moves to the next step by itself", async () => {
    const onNext = vi.fn();
    render(<Step steps={steps} index={0} urgency="emergency" onNext={onNext} onBack={() => {}} onLink={() => {}} onMoreInfo={() => {}} busy={false} readAloud onToggleRead={() => {}} />);
    await speakThrough();
    expect(spoken.map((u) => u.text)).toEqual(["Call 112 now.", "Do not wait to see if the pain passes."]);
    expect(spoken[0].lang).toBe("en-IN");
    expect(onNext).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(AUTO_NEXT_MS));
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("waits for the user on a step with a timer", async () => {
    const onNext = vi.fn();
    const timed: S[] = [{ ...base, id: "burns_fire_s2", text: "Cool the burn for at least 20 minutes.", do_not: [], aid: { kind: "timer", seconds: 1200 } }];
    render(<Step steps={[...timed, base]} index={0} urgency="emergency" onNext={onNext} onBack={() => {}} onLink={() => {}} onMoreInfo={() => {}} busy={false} readAloud onToggleRead={() => {}} />);
    await speakThrough();
    expect(spoken.at(-1)?.text).toMatch(/tap Done, next/);
    act(() => vi.advanceTimersByTime(60_000));
    expect(onNext).not.toHaveBeenCalled();
  });

  it("speaks Hindi steps with a Hindi voice", async () => {
    act(() => void i18n.changeLanguage("hi"));
    render(<Step steps={[{ ...base, text: "अभी 112 पर कॉल करें।", do_not: [] }]} index={0} urgency="emergency" onNext={() => {}} onBack={() => {}} onLink={() => {}} onMoreInfo={() => {}} busy={false} readAloud onToggleRead={() => {}} />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(spoken[0].text).toBe("अभी 112 पर कॉल करें।");
    expect(spoken[0].lang).toBe("hi-IN");
  });

  it("toggle button calls back", () => {
    const toggle = vi.fn();
    render(<Step steps={steps} index={0} urgency="emergency" onNext={() => {}} onBack={() => {}} onLink={() => {}} onMoreInfo={() => {}} busy={false} onToggleRead={toggle} />);
    fireEvent.click(screen.getByRole("button", { name: "Read steps aloud" }));
    expect(toggle).toHaveBeenCalled();
  });
});

describe("voice choice", () => {
  const v = (lang: string) => ({ lang, name: lang }) as SpeechSynthesisVoice;
  it("uses a Marathi voice when there is one, otherwise Hindi", () => {
    expect(pickVoice([v("en-US"), v("hi-IN"), v("mr-IN")], "mr")?.lang).toBe("mr-IN");
    expect(pickVoice([v("en-US"), v("hi-IN")], "mr")?.lang).toBe("hi-IN");
  });
  it("reads Hinglish with an Indian English voice", () => {
    expect(pickVoice([v("hi-IN"), v("en-IN")], "hinglish")?.lang).toBe("en-IN");
  });
  it("returns null when nothing fits, so the browser default is used", () => {
    expect(pickVoice([v("fr-FR")], "hi")).toBeNull();
  });
});
