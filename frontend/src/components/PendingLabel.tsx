import { useTranslation } from "react-i18next";

export function PendingLabel({ show }: { show: boolean }) {
  const { t } = useTranslation();
  if (!show) return null;
  return (
    <span className="mt-1 inline-block rounded-full bg-primary-soft px-2 py-0.5 text-note text-text-muted">{t("translation_pending")}</span>
  );
}
