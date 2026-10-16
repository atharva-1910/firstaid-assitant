import { Image as ImageIcon, PlayCircle } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Step, StepImage } from "../api/client";
import { useReducedMotion } from "./CprRhythm";
import { PendingLabel } from "./PendingLabel";

function Figure({ img, credit }: { img: StepImage; credit: string }) {
  return (
    <figure className="mt-4">
      {/* Pictures have their own white background, so they stay legible in dark mode. */}
      <img
        src={img.src}
        alt={img.alt}
        loading="lazy"
        className="mx-auto max-h-64 w-full rounded-card border border-border bg-white object-contain"
      />
      <figcaption className="mt-2 text-note text-text-muted">
        {credit}{" "}
        <a href={img.source_url} target="_blank" rel="noreferrer" className="text-primary underline">
          {img.author}
        </a>
        {" · "}
        <a href={img.license_url} target="_blank" rel="noreferrer" className="text-primary underline">
          {img.license}
        </a>
      </figcaption>
    </figure>
  );
}

export function StepCard({ step }: { step: Step }) {
  const { t } = useTranslation();
  const reduced = useReducedMotion();
  const img = step.image ?? null;
  const anim = step.animation ?? null;
  // The movement is shown first; with "reduce motion" on, the still picture is shown first instead.
  const [still, setStill] = useState(false);
  const showAnim = anim !== null && (img === null || (!still && !reduced) || (still && reduced));
  const shown = showAnim ? anim : img;
  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <p className="text-step font-semibold text-text" data-testid="step-text">
        {step.text}
      </p>
      <PendingLabel show={step.translation_pending} />
      {shown && <Figure img={shown} credit={showAnim ? t("animation_credit") : t("image_credit")} />}
      {anim && img && (
        <button
          type="button"
          onClick={() => setStill((s) => !s)}
          className="mt-2 inline-flex min-h-[44px] items-center gap-2 text-body text-primary underline"
        >
          {showAnim ? <ImageIcon aria-hidden size={18} /> : <PlayCircle aria-hidden size={18} />}
          {showAnim ? t("show_photo") : t("show_animation")}
        </button>
      )}
    </div>
  );
}
