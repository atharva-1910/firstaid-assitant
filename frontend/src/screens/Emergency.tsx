import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Explanation } from "../api/client";
import { PrimaryButton } from "../components/Buttons";
import { Call112Button } from "../components/Call112Button";
import { EmergencyBanner } from "../components/EmergencyBanner";

function Highlighted({ e }: { e: Explanation }) {
  return <strong className="font-semibold text-text">{e.word}</strong>;
}

export function Emergency({
  explanation,
  fallbackNote,
  onContinue,
  changedTo,
}: {
  explanation: Explanation[];
  fallbackNote: string | null;
  onContinue: () => void;
  changedTo?: string | null;
}) {
  const { t } = useTranslation();
  const [why, setWhy] = useState(false);
  return (
    <div className="flex flex-col gap-5">
      {changedTo ? <p className="rounded-card bg-primary-soft p-3 text-body text-text">{t("situation_changed", { name: changedTo })}</p> : null}
      <EmergencyBanner title={t("emergency_title")}>{t("emergency_body")}</EmergencyBanner>
      <Call112Button variant="large" />
      {explanation.length || fallbackNote ? (
        <div>
          <button onClick={() => setWhy((w) => !w)} aria-expanded={why} className="min-h-[44px] text-body text-primary underline">
            {t("why_alert")}
          </button>
          {why ? (
            <div className="mt-2 rounded-card border border-border bg-surface p-3 text-body text-text-muted">
              {explanation.length ? (
                <p>
                  {t("because_you_said")}{" "}
                  {explanation.map((e, i) => (
                    <span key={`${e.start}-${i}`}>
                      {i > 0 ? ", " : ""}
                      <Highlighted e={e} />
                    </span>
                  ))}
                </p>
              ) : (
                <p>{fallbackNote}</p>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
      <PrimaryButton onClick={onContinue}>{t("show_steps")}</PrimaryButton>
    </div>
  );
}
