import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Step } from "../api/client";
import { SOURCES } from "../sources";

function Chip({ children, onClick, pressed }: { children: React.ReactNode; onClick?: () => void; pressed?: boolean }) {
  const cls = "rounded-full border border-border bg-surface px-2.5 py-1 text-note text-text-muted";
  return onClick ? (
    <button type="button" onClick={onClick} aria-pressed={pressed} className={`${cls} underline decoration-dotted`}>
      {children}
    </button>
  ) : (
    <span className={cls}>{children}</span>
  );
}

export function SourceChips({ step }: { step: Step }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const src = step.source;
  const label =
    src.doc === "UNSOURCED"
      ? t("source_needed")
      : `${SOURCES[src.doc]?.short ?? src.doc}${src.page ? `, ${t("page", { page: src.page })}` : ""}`;
  const agreementKey = {
    agree: "sources_agree",
    differ: "sources_differ",
    single_source: "single_source",
    unchecked: "agreement_unchecked",
  }[step.agreement];
  const evidenceKey = `evidence_${step.evidence}`;
  const note = step.verify_note;
  return (
    <div>
      <div className="flex flex-wrap gap-2" aria-label="Sources">
        {src.doc !== "UNSOURCED" && SOURCES[src.doc] ? (
          <a href={SOURCES[src.doc].url} target="_blank" rel="noreferrer" className="rounded-full border border-border bg-surface px-2.5 py-1 text-note text-primary underline">
            {label}
          </a>
        ) : (
          <Chip>{label}</Chip>
        )}
        {step.also_in.map((s) => (
          <Chip key={`${s.doc}-${s.page}`}>
            {SOURCES[s.doc]?.short ?? s.doc}
            {s.page ? `, ${t("page", { page: s.page })}` : ""}
          </Chip>
        ))}
        <Chip onClick={step.agreement === "differ" || note ? () => setOpen((o) => !o) : undefined} pressed={open}>
          {t(agreementKey)}
        </Chip>
        <Chip>{t(evidenceKey)}</Chip>
        {!step.verified ? <Chip onClick={note ? () => setOpen((o) => !o) : undefined} pressed={open}>{t("not_verified")}</Chip> : null}
      </div>
      {open && note ? <p className="mt-2 rounded-card bg-primary-soft p-2 text-note text-text-muted">{note}</p> : null}
    </div>
  );
}
