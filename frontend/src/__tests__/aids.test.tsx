import { act, fireEvent, render, screen } from "@testing-library/react";

import { StepAid } from "../components/aids/StepAid";
import { clearAids } from "../components/aids/store";
import { Summary } from "../screens/Summary";
import "../i18n";

beforeEach(() => {
  clearAids();
  vi.useFakeTimers();
});
afterEach(() => vi.useRealTimers());

describe("step aids", () => {
  it("timer counts down the stated time and says when it is up", () => {
    render(<StepAid stepId="burns_fire_s2" aid={{ kind: "timer", seconds: 1200 }} />);
    expect(screen.getByText("20:00")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /start timer/i }));
    act(() => vi.advanceTimersByTime(61_000));
    expect(screen.getByText("18:59")).toBeTruthy();
    act(() => vi.advanceTimersByTime(20 * 60_000));
    expect(screen.getByText("Time is up.")).toBeTruthy();
  });

  it("keeps running when the user leaves the step and comes back", () => {
    const { unmount } = render(<StepAid stepId="bite_dog_s2" aid={{ kind: "timer", seconds: 900 }} />);
    fireEvent.click(screen.getByRole("button", { name: /start timer/i }));
    unmount();
    act(() => vi.advanceTimersByTime(5 * 60_000));
    render(<StepAid stepId="bite_dog_s2" aid={{ kind: "timer", seconds: 900 }} />);
    expect(screen.getByText("10:00")).toBeTruthy();
  });

  it("cycle counter moves from 5 back blows to 5 abdominal thrusts, then a new round", () => {
    const phases = [
      { key: "back_blows", count: 5, image: "/steps/ch_s4.webp" },
      { key: "abdominal_thrusts", count: 5, image: "/steps/ch_s5.webp" },
    ];
    render(<StepAid stepId="ch_s6" aid={{ kind: "cycle", phases }} />);
    expect(screen.getByText("Back blows: 0 / 5")).toBeTruthy();
    const tapBlow = screen.getByRole("button", { name: "Tap after each back blow" });
    for (let i = 0; i < 5; i++) fireEvent.click(tapBlow);
    expect(screen.getByText("Abdominal thrusts: 0 / 5")).toBeTruthy();
    const tapThrust = screen.getByRole("button", { name: "Tap after each abdominal thrust" });
    for (let i = 0; i < 5; i++) fireEvent.click(tapThrust);
    expect(screen.getByText("Round 2")).toBeTruthy();
    expect(screen.getByText("Back blows: 0 / 5")).toBeTruthy();
  });

  it("a noted bite time appears first in the handover summary", () => {
    vi.setSystemTime(new Date(2026, 9, 15, 21, 42));
    render(<StepAid stepId="bite_snake_s6" aid={{ kind: "note_time", key: "bite_time" }} />);
    fireEvent.click(screen.getByRole("button", { name: "The bite happened just now" }));
    expect(screen.getByText(/Bite time:/)).toBeTruthy();
    render(<Summary lines={["Situation: Bites"]} pending={false} onStartOver={() => undefined} />);
    const items = screen.getAllByRole("listitem").map((li) => li.textContent);
    expect(items[0]).toMatch(/^Time of bite: 9:42/i);
    expect(items[1]).toBe("Situation: Bites");
  });

  it("every aid string exists in all four languages", async () => {
    const langs = ["en", "hi", "hinglish", "mr"] as const;
    const files = await Promise.all(langs.map((l) => import(`../i18n/${l}.json`)));
    const keys = Object.keys(files[0].default).filter((k) => k.startsWith("aid_") || k.startsWith("summary_"));
    expect(keys.length).toBeGreaterThan(20);
    for (const f of files) for (const k of keys) expect(f.default[k], k).toBeTruthy();
  });
});
