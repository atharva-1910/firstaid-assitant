import { act, fireEvent, render, screen } from "@testing-library/react";

import i18n from "../i18n";
import { Home } from "../screens/Home";

type Handler = ((e: unknown) => void) | null;

class FakeRecognition {
  static last: FakeRecognition | null = null;
  lang = "";
  interimResults = false;
  continuous = false;
  maxAlternatives = 1;
  onresult: Handler = null;
  onerror: Handler = null;
  onend: (() => void) | null = null;
  started = false;
  constructor() {
    FakeRecognition.last = this;
  }
  start() {
    this.started = true;
  }
  stop() {
    this.onend?.();
  }
  abort() {
    this.onend?.();
  }
  say(...parts: string[]) {
    const results = parts.map((p) => Object.assign([{ transcript: p }], { isFinal: true }));
    this.onresult?.({ resultIndex: 0, results });
  }
}

const w = window as unknown as { webkitSpeechRecognition?: unknown };

afterEach(() => {
  delete w.webkitSpeechRecognition;
  FakeRecognition.last = null;
  act(() => void i18n.changeLanguage("en"));
});

describe("speech input", () => {
  it("hides the mic when the browser has no speech recognition", () => {
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    expect(screen.queryByRole("button", { name: /speak instead/i })).toBeNull();
  });

  it("puts speech after typed text and never submits by itself", () => {
    w.webkitSpeechRecognition = FakeRecognition;
    const onSubmit = vi.fn();
    render(<Home onSubmit={onSubmit} onAbout={() => {}} busy={false} />);
    const box = screen.getByRole("textbox") as HTMLTextAreaElement;
    fireEvent.change(box, { target: { value: "my father" } });

    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    expect(FakeRecognition.last?.started).toBe(true);
    // No language picked: listening starts in Hindi, the recogniser that copes best with all four.
    expect(FakeRecognition.last?.lang).toBe("hi-IN");
    act(() => FakeRecognition.last!.say("is not ", "breathing"));
    expect(box.value).toBe("my father is not breathing");
    expect(onSubmit).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /stop listening/i }));
    expect(screen.getByRole("button", { name: /speak instead/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));
    expect(onSubmit).toHaveBeenCalledWith("my father is not breathing");
  });

  it("listens in the selected language; Hinglish uses Hindi recognition", () => {
    w.webkitSpeechRecognition = FakeRecognition;
    act(() => void i18n.changeLanguage("hinglish"));
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} preferredLang="hinglish" />);
    fireEvent.click(screen.getByRole("button", { name: /bol kar batayein/i }));
    expect(FakeRecognition.last?.lang).toBe("hi-IN");
  });

  it("explains a blocked microphone", () => {
    w.webkitSpeechRecognition = FakeRecognition;
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    act(() => {
      FakeRecognition.last!.onerror?.({ error: "not-allowed" });
      FakeRecognition.last!.onend?.();
    });
    expect(screen.getByRole("status").textContent).toMatch(/microphone access is blocked/i);
  });

  it("hears Marathi and switches the recogniser to Marathi without being told", async () => {
    w.webkitSpeechRecognition = FakeRecognition;
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ lang: "mr", script: "devanagari", p: 0.99 })));
    vi.stubGlobal("fetch", fetchMock);
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    const first = FakeRecognition.last!;
    expect(first.lang).toBe("hi-IN");
    await act(async () => first.say("माझे वडील श्वास घेत नाहीत"));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const second = FakeRecognition.last!;
    expect(second).not.toBe(first);
    expect(second.lang).toBe("mr-IN");
    expect(screen.getByRole("status").textContent).toMatch(/Heard मराठी/);
    // What was heard before the switch is kept; new words follow it.
    act(() => second.say("लवकर सांगा"));
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).value).toBe("माझे वडील श्वास घेत नाहीत लवकर सांगा");
    vi.unstubAllGlobals();
  });

  it("hears English written in Devanagari, switches to English and asks for it again", async () => {
    w.webkitSpeechRecognition = FakeRecognition;
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ lang: "en", script: "devanagari", p: 0.99, transliterated: true }))));
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    const first = FakeRecognition.last!;
    expect(first.lang).toBe("hi-IN");
    await act(async () => first.say("माय फादर इज़ नॉट ब्रीदिंग"));
    const second = FakeRecognition.last!;
    expect(second).not.toBe(first);
    expect(second.lang).toBe("en-IN");
    // The Devanagari spelling of English is dropped, not sent on.
    const box = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(box.value).toBe("");
    expect(screen.getByRole("status").textContent).toMatch(/please say it again/i);
    act(() => second.say("my father is not breathing"));
    expect(box.value).toBe("my father is not breathing");
    vi.unstubAllGlobals();
  });

  it("does not switch when the language model is unsure", async () => {
    w.webkitSpeechRecognition = FakeRecognition;
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ lang: "mr", script: "devanagari", p: 0.58 }))));
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    const first = FakeRecognition.last!;
    await act(async () => first.say("माय फादर इज नॉट ब्रीदिंग"));
    expect(FakeRecognition.last).toBe(first);
    expect(first.lang).toBe("hi-IN");
    vi.unstubAllGlobals();
  });

  it("keeps listening in the current language if the language check fails (offline)", async () => {
    w.webkitSpeechRecognition = FakeRecognition;
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("offline"); }));
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: /speak instead/i }));
    const first = FakeRecognition.last!;
    await act(async () => first.say("my father is not breathing"));
    expect(FakeRecognition.last).toBe(first);
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).value).toBe("my father is not breathing");
    vi.unstubAllGlobals();
  });
});
