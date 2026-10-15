import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "../App";
import type { AnalyzeResponse } from "../api/client";
import { buildQueue } from "../flow";
import "../i18n";

const base: AnalyzeResponse = {
  session_id: "s1",
  detected_lang: "en",
  display_lang: "en",
  next_screen: "steps",
  urgency: "home",
  situation: { id: "burns", name: "Burns", branch: "fire_heat", confidence: 0.9 },
  situation_changed: null,
  provisional: false,
  child_or_infant: false,
  out_of_scope: false,
  out_of_scope_note: null,
  clarifying_question: null,
  explanation: [],
  fallback_note: null,
  harmful_action: null,
  slots: {},
  uncertain: [],
  steps: [
    {
      id: "a", order: 1, text: "First step.", translation_pending: false, rephrased: false, source: { doc: "G1", page: 288 }, also_in: [],
      agreement: "unchecked", evidence: "unchecked", verified: false, cpr_rhythm: false, link: null, do_not: [],
    },
    {
      id: "b", order: 2, text: "Second step.", translation_pending: false, rephrased: false, source: { doc: "G2", page: null }, also_in: [],
      agreement: "unchecked", evidence: "unchecked", verified: false, cpr_rhythm: true, link: null,
      do_not: [{ text: "Do not use ice.", reason: "It can damage the skin further.", translation_pending: false }],
    },
  ],
  do_not: [],
  actions_taken: [],
  disclaimer: "",
};

describe("buildQueue", () => {
  it("puts Call 112 first, then the warning, then steps", () => {
    const harmful = { id: "m", action: "x", reason: "y", word: "z", translation_pending: false };
    expect(buildQueue({ ...base, next_screen: "emergency", harmful_action: harmful })).toEqual(["emergency", "harmful_warning", "steps"]);
  });
  it("child goes straight to the child screen", () => {
    expect(buildQueue({ ...base, child_or_infant: true, next_screen: "child" })).toEqual(["child"]);
  });
  it("asks the question before steps", () => {
    const q = { id: "q", text: "?", translation_pending: false, safety: true, options: [] };
    expect(buildQueue({ ...base, next_screen: "emergency", clarifying_question: q })).toEqual(["emergency", "question"]);
  });
  it("out of scope after the emergency screen", () => {
    expect(buildQueue({ ...base, next_screen: "emergency", out_of_scope: true, steps: [] })).toEqual(["emergency", "out_of_scope"]);
  });
});

describe("App", () => {
  beforeEach(() => {
    window.matchMedia = ((q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
    window.scrollTo = () => undefined;
  });

  it("shows Call 112 on the home screen", () => {
    render(<App />);
    expect(screen.getByText("What happened?")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Call 112/ })[0]).toHaveAttribute("href", "tel:112");
  });

  it("walks from emergency to one step at a time", async () => {
    const body = { ...base, next_screen: "emergency", urgency: "emergency", explanation: [{ word: "not breathing", start: 0, end: 13, weight: 1, text: "not breathing" }] };
    globalThis.fetch = vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })) as unknown as typeof fetch;
    render(<App />);
    fireEvent.change(screen.getByLabelText("What happened?"), { target: { value: "not breathing" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await waitFor(() => expect(screen.getByText("This is an emergency")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /Call 112 now/ })).toHaveAttribute("href", "tel:112");
    fireEvent.click(screen.getByText("Why this alert?"));
    expect(screen.getByText("not breathing")).toBeInTheDocument();
    fireEvent.click(screen.getByText("While you wait: show me what to do"));
    expect(screen.getByTestId("step-text")).toHaveTextContent("First step.");
    expect(screen.getByText("Step 1 of 2")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Call 112/ }).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /Done, next/ }));
    expect(screen.getByTestId("step-text")).toHaveTextContent("Second step.");
    expect(screen.getByText("Do not use ice.")).toBeInTheDocument();
    expect(screen.getByText("Push down each time the circle grows.")).toBeInTheDocument();
  });
});
