import { useTranslation } from "react-i18next";

import { SecondaryButton } from "../components/Buttons";
import { Call112Button } from "../components/Call112Button";

export function OutOfScope({ note, fallback, onStartOver }: { note: string | null; fallback: boolean; onStartOver: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-step font-semibold text-text">{fallback ? t("fallback_title") : t("oos_title")}</h1>
      {note ? <p className="rounded-card bg-primary-soft p-3 text-body text-text">{note}</p> : null}
      <p className="text-body text-text">{t("oos_text")}</p>
      <Call112Button variant="large" />
      <SecondaryButton onClick={onStartOver}>{t("start_over")}</SecondaryButton>
    </div>
  );
}
