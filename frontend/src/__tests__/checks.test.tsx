import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "../App";
import type { AnalyzeResponse, Step } from "../api/client";
import "../i18n";

const mk = (id: string, text: string, extra: Partial<Step> = {}): Step => ({
  id, order: 1, text, translation_pending: false, rephrased: false, source: { doc: "G3", page: null }, also_in: [],
  agreement: "unchecked", evidence: "unchecked", verified: false, cpr_rhythm: false, link: null, do_not: [], ...extra,
});

const s6 = mk("ch_s6", "Keep repeating back blows and abdominal thrusts.", {
  check: {
    question: "Has the object come out?",
    translation_pending: false,
    options: [
      { id: "yes", label: "Yes", go: { step: "ch_s8" }, set: {}, emergency: false },
      { id: "not_yet", label: "Not yet", go: "stay", set: {}, emergency: false },
      { id: "unresponsive", label: "They became unresponsive", go: { situation: "unresponsive", branch: "path_a", step: "unr_a1" }, set: {}, emergency: false },
    ],
  },
});
const steps = [s6, mk("ch_s7", "If they become unresponsive, start CPR."), mk("ch_s8", "They should see a doctor.")];

const resp: AnalyzeResponse = {
  session_id: "s1", detected_lang: "en", display_lang: "en", next_screen: "steps", urgency: "emergency",
  situation: { id: "choking", name: "Choking", branch: "default", confidence: 1 }, situation_changed: null, provisional: false,
  child_or_infant: false, out_of_scope: false, out_of_scope_note: null, clarifying_question: null, explanation: [],
  fallback_note: null, harmful_action: null, slots: {}, uncertain: [], steps, do_not: [], actions_taken: [], disclaimer: "",
};

const cprView = {
  id: "unresponsive", name: "Unresponsive", owner: "", review_status: "draft", branch: "path_a", branches: ["path_a", "path_b"],
  recognition: [], urgency: "emergency", do_not: [], source_differences: [],
  steps: [mk("unr_s1", "Make sure the area is safe."), mk("unr_a1", "Call 112 now and put the phone on speaker.")],
};

async function openSteps() {
  globalThis.fetch = vi.fn(async (url: RequestInfo | URL) => {
    const u = String(url);
    const body = u.includes("/api/situations/unresponsive") ? cprView : resp;
    return new Response(JSON.stringify(body), { status: 200 });
  }) as unknown as typeof fetch;
  render(<App />);
  fireEvent.change(screen.getByLabelText("What happened?"), { target: { value: "he is choking" } });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  await waitFor(() => expect(screen.getByText("Has the object come out?")).toBeInTheDocument());
}

describe("step checks (Yes / No)", () => {
  beforeEach(() => {
    window.matchMedia = ((q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
    window.scrollTo = () => undefined;
  });

  it("Yes jumps to the step the answer points at, and Back returns along that path", async () => {
    await openSteps();
    fireEvent.click(screen.getByRole("button", { name: "Yes" }));
    expect(screen.getByText("They should see a doctor.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Back/ }));
    expect(screen.getByText("Has the object come out?")).toBeInTheDocument();
  });

  it("Not yet keeps the person on the step and says so", async () => {
    await openSteps();
    fireEvent.click(screen.getByRole("button", { name: "Not yet" }));
    expect(screen.getByText("Keep repeating back blows and abdominal thrusts.")).toBeInTheDocument();
    expect(screen.getByText(/Keep doing this step/)).toBeInTheDocument();
  });

  it("an answer that changes the situation opens the CPR steps at the right step", async () => {
    await openSteps();
    fireEvent.click(screen.getByRole("button", { name: "They became unresponsive" }));
    await waitFor(() => expect(screen.getByText("Call 112 now and put the phone on speaker.")).toBeInTheDocument());
  });

  it("Done, next still works on a step with a check", async () => {
    await openSteps();
    fireEvent.click(screen.getByRole("button", { name: /Done, next/ }));
    expect(screen.getByText("If they become unresponsive, start CPR.")).toBeInTheDocument();
  });
});
