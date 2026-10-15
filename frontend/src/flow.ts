// Turns an API response into the ordered list of screens to show.
// Order (Section 7.1): Call 112 first, then any harmful-action warning, then the
// out-of-scope note, the clarifying question, or the steps. One thing per screen.
import type { AnalyzeResponse } from "./api/client";

export type Screen =
  | "home"
  | "question"
  | "emergency"
  | "harmful_warning"
  | "steps"
  | "summary"
  | "child"
  | "out_of_scope"
  | "about";

export function buildQueue(r: AnalyzeResponse): Screen[] {
  if (r.child_or_infant) return ["child"];
  const q: Screen[] = [];
  if (r.next_screen === "emergency") q.push("emergency");
  if (r.harmful_action) q.push("harmful_warning");
  if (r.out_of_scope) q.push("out_of_scope");
  else if (r.clarifying_question) q.push("question");
  else if (r.steps.length) q.push("steps");
  else if (!q.length) q.push("out_of_scope");
  return q;
}
