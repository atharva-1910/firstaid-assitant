// Typed client for the backend API (Section 13.2). The Vite dev server proxies /api to FastAPI.

export type Lang = "en" | "hi" | "hinglish" | "mr";
export type UiLang = Lang | "auto";
export type Urgency = "emergency" | "clinic" | "home";
export type ScreenName = "question" | "emergency" | "steps" | "harmful_warning" | "child" | "out_of_scope" | "summary";

export interface Source {
  doc: string;
  page: number | null;
}

export interface DoNot {
  text: string;
  reason: string;
  translation_pending: boolean;
  step?: string | null;
}

export interface Step {
  id: string;
  order: number;
  text: string;
  translation_pending: boolean;
  rephrased: boolean;
  source: Source;
  also_in: Source[];
  agreement: "agree" | "differ" | "single_source" | "unchecked";
  evidence: "strong" | "weak" | "good_practice" | "unchecked";
  verified: boolean;
  verify_note?: string | null;
  cpr_rhythm: boolean;
  link?: { situation: string; branch?: string } | null;
  do_not: DoNot[];
}

export interface Question {
  id: string;
  text: string;
  translation_pending: boolean;
  safety: boolean;
  options: { id: string; label: string; translation_pending: boolean }[];
}

export interface Explanation {
  word: string;
  start: number;
  end: number;
  weight: number;
  text: string;
}

export interface HarmfulAction {
  id: string;
  action: string;
  reason: string;
  word: string;
  source?: string;
  translation_pending: boolean;
}

export interface AnalyzeResponse {
  session_id: string;
  detected_lang: Lang;
  display_lang: Lang;
  next_screen: ScreenName;
  urgency: Urgency;
  situation: { id: string; name: string; branch: string | null; confidence: number };
  situation_changed: { from: string; to: string } | null;
  provisional: boolean;
  child_or_infant: boolean;
  out_of_scope: boolean;
  out_of_scope_note: string | null;
  clarifying_question: Question | null;
  explanation: Explanation[];
  fallback_note: string | null;
  harmful_action: HarmfulAction | null;
  slots: Record<string, string>;
  uncertain: string[];
  steps: Step[];
  do_not: DoNot[];
  actions_taken: string[];
  disclaimer: string;
}

export interface SituationView {
  id: string;
  name: string;
  branch: string;
  urgency: Urgency | null;
  steps: Step[];
  do_not: DoNot[];
}

export interface SummaryResponse {
  session_id: string;
  lines: string[];
  text: string;
  translation_pending: boolean;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, String(detail));
  }
  return (await res.json()) as T;
}

export const api = {
  analyze: (text: string, sessionId: string | null, uiLang: UiLang) =>
    request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, text, ui_lang: uiLang }),
    }),
  answer: (sessionId: string, questionId: string, answerId: string, uiLang: UiLang) =>
    request<AnalyzeResponse>("/api/answer", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, question_id: questionId, answer_id: answerId, ui_lang: uiLang }),
    }),
  situation: (id: string, lang: Lang, branch?: string | null) =>
    request<SituationView>(`/api/situations/${id}?lang=${lang}${branch ? `&branch=${encodeURIComponent(branch)}` : ""}`),
  summary: (sessionId: string, uiLang: UiLang, completedSteps: number) =>
    request<SummaryResponse>("/api/summary", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, ui_lang: uiLang, completed_steps: completedSteps }),
    }),
};
