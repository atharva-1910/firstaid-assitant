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
    expect(FakeRecognition.last?.lang).toBe("en-IN");
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
    render(<Home onSubmit={() => {}} onAbout={() => {}} busy={false} />);
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
});
