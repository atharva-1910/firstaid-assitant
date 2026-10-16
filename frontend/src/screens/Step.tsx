import { ArrowLeft, ArrowRight, HeartPulse, RotateCcw, Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { CheckOption, Lang, Step as S, Urgency } from "../api/client";
import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { StepAid } from "../components/aids/StepAid";
import { CprRhythm } from "../components/CprRhythm";
import { DoNotBox } from "../components/DoNotBox";
import { ProgressBar } from "../components/ProgressBar";
import { SourceChips } from "../components/SourceChips";
import { StepCard } from "../components/StepCard";
import { UrgencyNote } from "../components/UrgencyNote";
import { speakAll, stopSpeaking, ttsSupported, useVoices } from "../tts";

export const AUTO_NEXT_MS = 3000; // pause after reading a step before moving on, so there is time to act

/** Steps that take time (a timer, CPR, a counter, a link to CPR), steps that ask a check, or the last step:
 *  read it, then wait for the user. */
export function waitsForUser(step: S, last: boolean): boolean {
  return last || Boolean(step.aid) || step.cpr_rhythm || Boolean(step.link) || Boolean(step.check);
}

export function Step({
  steps,
  index,
  urgency,
  onNext,
  onBack,
  onLink,
  onCheck,
  onMoreInfo,
  busy,
  banner,
  readAloud = false,
  onToggleRead,
}: {
  steps: S[];
  index: number;
  urgency: Urgency;
  onNext: () => void;
  onBack: () => void;
  onLink: (situation: string, branch?: string) => void;
  onCheck?: (option: CheckOption) => void;
  onMoreInfo: (text: string) => void;
  busy: boolean;
  banner?: string | null;
  readAloud?: boolean;
  onToggleRead?: () => void;
}) {
  const { t, i18n } = useTranslation();
  const [more, setMore] = useState(false);
  const [text, setText] = useState("");
  const [again, setAgain] = useState(0);
  const [stayed, setStayed] = useState<string | null>(null); // the answer that keeps the person on this step
  useEffect(() => setStayed(null), [index, steps]);
  const voices = useVoices();
  const voicesRef = useRef(voices);
  voicesRef.current = voices;
  const onNextRef = useRef(onNext);
  onNextRef.current = onNext;
  const step = steps[index];
  const last = index === steps.length - 1;
  const uiLang = i18n.language as Lang;

  // Read the step aloud, then its warnings; then move on by itself, unless the step takes time.
  useEffect(() => {
    if (!readAloud || !step || !ttsSupported()) return;
    const signal = { cancelled: false };
    let timer: number | undefined;
    stopSpeaking();
    const parts = [
      { text: step.text, lang: step.translation_pending ? ("en" as Lang) : uiLang },
      ...step.do_not.map((d) => ({ text: d.text, lang: d.translation_pending ? ("en" as Lang) : uiLang })),
    ];
    const wait = waitsForUser(step, last);
    if (step.check) {
      const cl = step.check.translation_pending ? ("en" as Lang) : uiLang;
      parts.push({ text: step.check.question, lang: cl }, { text: step.check.options.map((o) => o.label).join(". "), lang: cl });
    } else if (wait) parts.push({ text: t("tts_tap_next"), lang: uiLang });
    speakAll(parts, voicesRef.current, signal).then(() => {
      if (!signal.cancelled && !wait) timer = window.setTimeout(() => onNextRef.current(), AUTO_NEXT_MS);
    });
    return () => {
      signal.cancelled = true;
      window.clearTimeout(timer);
      stopSpeaking();
    };
  }, [readAloud, step, last, uiLang, again, t]);

  if (!step) return null;
  return (
    <div className="flex flex-col gap-4">
      {banner ? <p className="rounded-card bg-primary-soft p-3 text-body text-text">{banner}</p> : null}
      {index === 0 ? <UrgencyNote urgency={urgency} /> : null}
      <ProgressBar n={index + 1} total={steps.length} />
      {ttsSupported() && onToggleRead ? (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onToggleRead}
            aria-pressed={readAloud}
            className={`inline-flex min-h-[48px] items-center gap-2 rounded-full px-4 text-body font-semibold focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 ${
              readAloud ? "bg-primary text-surface" : "border border-border bg-surface text-primary"
            }`}
          >
            {readAloud ? <Volume2 aria-hidden size={20} /> : <VolumeX aria-hidden size={20} />}
            {readAloud ? t("tts_off") : t("tts_on")}
          </button>
          {readAloud ? (
            <button type="button" onClick={() => setAgain((n) => n + 1)} className="inline-flex min-h-[48px] items-center gap-2 px-2 text-body text-primary underline">
              <RotateCcw aria-hidden size={18} />
              {t("tts_again")}
            </button>
          ) : null}
          {readAloud ? <p className="w-full text-note text-text-muted">{t("tts_auto_note")}</p> : null}
        </div>
      ) : null}
      <StepCard step={step} />
      {step.cpr_rhythm ? <CprRhythm /> : null}
      {step.aid ? <StepAid key={step.id} stepId={step.id} aid={step.aid} /> : null}
      <DoNotBox items={step.do_not} />
      <SourceChips step={step} />
      {step.link ? (
        <SecondaryButton onClick={() => onLink(step.link!.situation, step.link!.branch)}>
          <HeartPulse aria-hidden size={20} />
          {t("show_cpr")}
        </SecondaryButton>
      ) : null}
      {step.check && onCheck ? (
        <fieldset className="flex flex-col gap-3 rounded-card border-2 border-primary bg-surface p-4">
          <legend className="px-1 text-body font-semibold text-text">{step.check.question}</legend>
          {step.check.options.map((o) => {
            const chosen = stayed === o.id;
            const Btn = o.go === "stay" ? SecondaryButton : PrimaryButton;
            return (
              <Btn
                key={o.id}
                aria-pressed={chosen || undefined}
                onClick={() => {
                  if (o.go === "stay") setStayed(o.id);
                  onCheck(o);
                }}
              >
                {o.label}
              </Btn>
            );
          })}
          {stayed ? <p className="text-body text-text-muted" role="status">{t("check_stay")}</p> : null}
        </fieldset>
      ) : null}
      <div className="grid grid-cols-[1fr_2fr] gap-3">
        <SecondaryButton onClick={onBack}>
          <ArrowLeft aria-hidden size={20} />
          {t("back")}
        </SecondaryButton>
        {step.check && onCheck ? (
          <SecondaryButton onClick={onNext}>
            {last ? t("finish") : t("next")}
            {!last ? <ArrowRight aria-hidden size={20} /> : null}
          </SecondaryButton>
        ) : (
          <PrimaryButton onClick={onNext}>
            {last ? t("finish") : t("next")}
            {!last ? <ArrowRight aria-hidden size={20} /> : null}
          </PrimaryButton>
        )}
      </div>
      <div className="pt-2">
        {more ? (
          <form
            className="flex flex-col gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (text.trim()) {
                onMoreInfo(text.trim());
                setText("");
                setMore(false);
              }
            }}
          >
            <textarea
              rows={2}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t("own_words")}
              className="w-full resize-none rounded-card border border-border bg-surface p-3 text-body text-text focus:border-primary focus:outline-none"
            />
            <SecondaryButton type="submit" disabled={busy || !text.trim()}>
              {t("send")}
            </SecondaryButton>
          </form>
        ) : (
          <button onClick={() => setMore(true)} className="min-h-[44px] text-body text-primary underline">
            {t("something_changed")}
          </button>
        )}
      </div>
      <p className="text-center text-note text-text-muted">{t("reassure")}</p>
    </div>
  );
}
