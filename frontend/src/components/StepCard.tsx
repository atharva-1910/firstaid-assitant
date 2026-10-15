import { useTranslation } from "react-i18next";

import type { Step } from "../api/client";
import { PendingLabel } from "./PendingLabel";

export function StepCard({ step }: { step: Step }) {
  const { t } = useTranslation();
  const img = step.image;
  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <p className="text-step font-semibold text-text" data-testid="step-text">
        {step.text}
      </p>
      <PendingLabel show={step.translation_pending} />
      {img && (
        <figure className="mt-4">
          {/* Illustrations have their own white background, so they stay legible in dark mode. */}
          <img
            src={img.src}
            alt={img.alt}
            loading="lazy"
            className="mx-auto max-h-64 w-full rounded-card border border-border bg-white object-contain"
          />
          <figcaption className="mt-2 text-note text-text-muted">
            {t("image_credit")}{" "}
            <a href={img.source_url} target="_blank" rel="noreferrer" className="text-primary underline">
              {img.author}
            </a>
            {" · "}
            <a href={img.license_url} target="_blank" rel="noreferrer" className="text-primary underline">
              {img.license}
            </a>
          </figcaption>
        </figure>
      )}
    </div>
  );
}
