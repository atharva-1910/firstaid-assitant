import { ArrowLeft, ArrowRight, HeartPulse } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Step as S, Urgency } from "../api/client";
import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { CprRhythm } from "../components/CprRhythm";
import { DoNotBox } from "../components/DoNotBox";
import { ProgressBar } from "../components/ProgressBar";
import { SourceChips } from "../components/SourceChips";
import { StepCard } from "../components/StepCard";
import { UrgencyNote } from "../components/UrgencyNote";

export function Step({
  steps,
  index,
  urgency,
  onNext,
  onBack,
  onLink,
  onMoreInfo,
  busy,
  banner,
}: {
  steps: S[];
  index: number;
  urgency: Urgency;
  onNext: () => void;
  onBack: () => void;
  onLink: (situation: string, branch?: string) => void;
  onMoreInfo: (text: string) => void;
  busy: boolean;
  banner?: string | null;
}) {
  const { t } = useTranslation();
  const [more, setMore] = useState(false);
  const [text, setText] = useState("");
  const step = steps[index];
  if (!step) return null;
  const last = index === steps.length - 1;
  return (
    <div className="flex flex-col gap-4">
      {banner ? <p className="rounded-card bg-primary-soft p-3 text-body text-text">{banner}</p> : null}
      {index === 0 ? <UrgencyNote urgency={urgency} /> : null}
      <ProgressBar n={index + 1} total={steps.length} />
      <StepCard step={step} />
      {step.cpr_rhythm ? <CprRhythm /> : null}
      <DoNotBox items={step.do_not} />
      <SourceChips step={step} />
      {step.link ? (
        <SecondaryButton onClick={() => onLink(step.link!.situation, step.link!.branch)}>
          <HeartPulse aria-hidden size={20} />
          {t("show_cpr")}
        </SecondaryButton>
      ) : null}
      <div className="grid grid-cols-[1fr_2fr] gap-3">
        <SecondaryButton onClick={onBack}>
          <ArrowLeft aria-hidden size={20} />
          {t("back")}
        </SecondaryButton>
        <PrimaryButton onClick={onNext}>
          {last ? t("finish") : t("next")}
          {!last ? <ArrowRight aria-hidden size={20} /> : null}
        </PrimaryButton>
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
