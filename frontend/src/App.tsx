import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type AnalyzeResponse, type Lang, type Step as StepT, type Urgency } from "./api/client";
import { PrimaryButton } from "./components/Buttons";
import { clearAids } from "./components/aids/store";
import { Call112Button } from "./components/Call112Button";
import { Header } from "./components/Header";
import { buildQueue, type Screen } from "./flow";
import i18n, { scriptOf } from "./i18n";
import { About } from "./screens/About";
import { Child } from "./screens/Child";
import { Emergency } from "./screens/Emergency";
import { HarmfulWarning } from "./screens/HarmfulWarning";
import { Home } from "./screens/Home";
import { OutOfScope } from "./screens/OutOfScope";
import { Question } from "./screens/Question";
import { Step } from "./screens/Step";
import { Summary } from "./screens/Summary";

export default function App() {
  const { t } = useTranslation();
  const [lang, setLang] = useState<Lang>("en");
  const [langChosen, setLangChosen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [resp, setResp] = useState<AnalyzeResponse | null>(null);
  const [screen, setScreen] = useState<Screen>("home");
  const [queue, setQueue] = useState<Screen[]>([]);
  const [history, setHistory] = useState<Screen[]>([]);
  const [steps, setSteps] = useState<StepT[]>([]);
  const [stepView, setStepView] = useState<{ situation: string; branch: string | null } | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [urgency, setUrgency] = useState<Urgency>("home");
  const [completed, setCompleted] = useState(0);
  const [summary, setSummary] = useState<{ lines: string[]; pending: boolean }>({ lines: [], pending: false });
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<(() => void) | null>(null);
  // Read-aloud is remembered on this device; storage can be blocked, so every access is guarded.
  const [readAloud, setReadAloud] = useState<boolean>(() => {
    try {
      return window.localStorage.getItem("readAloud") === "1";
    } catch {
      return false;
    }
  });
  const toggleRead = () =>
    setReadAloud((on) => {
      try {
        window.localStorage.setItem("readAloud", on ? "0" : "1");
      } catch {
        /* storage blocked */
      }
      return !on;
    });

  // Language and script on <html>, so Devanagari gets its font and 1.6 line height.
  useEffect(() => {
    i18n.changeLanguage(lang);
    document.documentElement.lang = lang === "hinglish" ? "hi-Latn" : lang;
    document.documentElement.dataset.script = scriptOf(lang);
  }, [lang]);

  const uiLang = langChosen ? lang : "auto";

  const go = useCallback(
    (next: Screen) => {
      setHistory((h) => (screen === next ? h : [...h, screen]));
      setScreen(next);
      window.scrollTo?.({ top: 0 });
    },
    [screen],
  );

  const handle = useCallback(
    (r: AnalyzeResponse) => {
      setResp(r);
      setSessionId(r.session_id);
      if (!langChosen) setLang(r.display_lang);
      setUrgency(r.urgency);
      const sameSteps = steps.length > 0 && r.steps.length > 0 && steps.map((s) => s.id).join() === r.steps.map((s) => s.id).join();
      setSteps(r.steps);
      setStepView(r.situation.branch ? { situation: r.situation.id, branch: r.situation.branch } : null);
      if (!sameSteps) setStepIndex(0);
      setBanner(r.situation_changed ? t("situation_changed", { name: r.situation.name }) : null);
      const q = buildQueue(r);
      setQueue(q.slice(1));
      go(q[0]);
    },
    [langChosen, steps, go, t],
  );

  const run = useCallback(async (fn: () => Promise<void>, retry: () => void) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setLastAction(() => retry);
    } finally {
      setBusy(false);
    }
  }, []);

  const submit = (text: string) => run(async () => handle(await api.analyze(text, sessionId, uiLang)), () => submit(text));

  const answer = (optionId: string) => {
    if (!resp?.clarifying_question || !sessionId) return;
    const qid = resp.clarifying_question.id;
    run(async () => handle(await api.answer(sessionId, qid, optionId, uiLang)), () => answer(optionId));
  };

  const advance = () => {
    const [next, ...rest] = queue;
    setQueue(rest);
    go(next ?? (steps.length ? "steps" : "home"));
  };

  const showSummary = () =>
    run(async () => {
      if (!sessionId) return;
      const s = await api.summary(sessionId, uiLang, completed + 1);
      setSummary({ lines: s.lines, pending: s.translation_pending });
      go("summary");
    }, showSummary);

  const nextStep = () => {
    setCompleted((c) => Math.max(c, stepIndex + 1));
    if (stepIndex < steps.length - 1) setStepIndex((i) => i + 1);
    else showSummary();
  };

  const backStep = () => {
    if (stepIndex > 0) {
      setStepIndex((i) => i - 1);
      return;
    }
    const prev = history.filter((s) => s !== "steps").pop();
    setScreen(prev ?? "home");
  };

  const openLink = (situation: string, branch?: string) =>
    run(async () => {
      const view = await api.situation(situation, lang, branch);
      setSteps(view.steps);
      setStepView({ situation, branch: branch ?? null });
      setUrgency("emergency");
      const start = branch === "path_a" ? Math.max(0, view.steps.findIndex((s) => s.id.startsWith("unr_a"))) : 0;
      setStepIndex(start);
      setBanner(t("situation_changed", { name: view.name }));
    }, () => openLink(situation, branch));

  const changeLang = (l: Lang) => {
    setLang(l);
    setLangChosen(true);
    // Re-load the steps in the new language from the verified records (never translated in the app).
    if (stepView && screen === "steps") {
      api
        .situation(stepView.situation, l, stepView.branch)
        .then((v) => {
          if (v.steps.length === steps.length) setSteps(v.steps);
        })
        .catch(() => undefined);
    }
    if (screen === "summary" && sessionId) {
      api.summary(sessionId, l, completed).then((s) => setSummary({ lines: s.lines, pending: s.translation_pending })).catch(() => undefined);
    }
  };

  const startOver = () => {
    clearAids();
    setSessionId(null);
    setResp(null);
    setSteps([]);
    setStepView(null);
    setStepIndex(0);
    setQueue([]);
    setHistory([]);
    setCompleted(0);
    setBanner(null);
    setError(null);
    setScreen("home");
  };

  let body: JSX.Element | null = null;
  if (error) {
    body = (
      <div className="flex flex-col gap-4">
        <p className="rounded-card border border-border bg-surface p-4 text-body text-text">{t("error")}</p>
        <Call112Button variant="large" />
        <PrimaryButton onClick={() => lastAction?.()}>{t("try_again")}</PrimaryButton>
      </div>
    );
  } else if (screen === "home") {
    body = <Home onSubmit={submit} onAbout={() => go("about")} busy={busy} preferredLang={langChosen ? lang : null} />;
  } else if (screen === "about") {
    body = (
      <About
        onBack={() => {
          setScreen(history[history.length - 1] ?? "home");
          setHistory((h) => h.slice(0, -1));
        }}
      />
    );
  } else if (screen === "question" && resp?.clarifying_question) {
    body = <Question question={resp.clarifying_question} onAnswer={answer} busy={busy} />;
  } else if (screen === "emergency" && resp) {
    body = <Emergency explanation={resp.explanation} fallbackNote={resp.fallback_note} onContinue={advance} changedTo={banner ? resp.situation.name : null} />;
  } else if (screen === "harmful_warning" && resp?.harmful_action) {
    body = <HarmfulWarning harmful={resp.harmful_action} onContinue={advance} />;
  } else if (screen === "steps" && steps.length) {
    body = (
      <Step
        steps={steps}
        index={stepIndex}
        urgency={urgency}
        onNext={nextStep}
        onBack={backStep}
        onLink={openLink}
        onMoreInfo={submit}
        busy={busy}
        banner={banner}
        readAloud={readAloud}
        onToggleRead={toggleRead}
      />
    );
  } else if (screen === "summary") {
    body = <Summary lines={summary.lines} pending={summary.pending} onStartOver={startOver} />;
  } else if (screen === "child") {
    body = <Child onStartOver={startOver} />;
  } else if (screen === "out_of_scope") {
    body = <OutOfScope note={resp?.out_of_scope_note ?? null} fallback={Boolean(resp?.fallback_note)} onStartOver={startOver} />;
  } else {
    body = <Home onSubmit={submit} onAbout={() => go("about")} busy={busy} preferredLang={langChosen ? lang : null} />;
  }

  return (
    <div className="min-h-screen bg-bg font-sans text-text">
      <Header lang={lang} onLang={changeLang} onHome={startOver} />
      <main className="mx-auto max-w-column px-4 py-6">
        <div key={`${screen}-${stepIndex}-${error ? 1 : 0}`} className="screen-fade" aria-live="polite" aria-busy={busy}>
          {body}
        </div>
      </main>
    </div>
  );
}
