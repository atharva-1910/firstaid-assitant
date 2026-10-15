import { useTranslation } from "react-i18next";

import { SecondaryButton } from "../components/Buttons";
import { SOURCES, TEAM } from "../sources";

export function About({ onBack }: { onBack: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-step font-semibold text-text">{t("about_title")}</h1>
      <p className="text-body text-text">{t("about_intro")}</p>
      <section>
        <h2 className="mb-2 text-question font-semibold text-text">{t("sources")}</h2>
        <ul className="space-y-3">
          {Object.entries(SOURCES).map(([id, s]) => (
            <li key={id} className="rounded-card border border-border bg-surface p-4">
              <a href={s.url} target="_blank" rel="noreferrer" className="text-body font-semibold text-primary underline">
                {id}. {s.title}
              </a>
              <p className="text-note text-text-muted">
                {s.publisher}, {s.year}
              </p>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="mb-2 text-question font-semibold text-text">{t("team")}</h2>
        <ul className="space-y-2">
          {TEAM.map((m) => (
            <li key={m.prn} className="text-body text-text">
              <span className="font-semibold">{m.name}</span> <span className="text-note text-text-muted">({m.prn})</span>
              <span className="block text-note text-text-muted">{m.role}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-note text-text-muted">CCNLP Mini Project, MIT World Peace University, Pune</p>
      </section>
      <p className="rounded-card bg-primary-soft p-3 text-body text-text">{t("disclaimer")}</p>
      <SecondaryButton onClick={onBack}>{t("back")}</SecondaryButton>
    </div>
  );
}
