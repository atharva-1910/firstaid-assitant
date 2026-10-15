import { useTranslation } from "react-i18next";

export function ProgressBar({ n, total }: { n: number; total: number }) {
  const { t } = useTranslation();
  const pct = total ? Math.round((n / total) * 100) : 0;
  return (
    <div>
      <p className="text-note font-semibold text-text-muted">{t("step_of", { n, total })}</p>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-primary-soft" role="progressbar" aria-valuemin={1} aria-valuemax={total} aria-valuenow={n}>
        <div className="h-full rounded-full bg-primary transition-[width] duration-150" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
