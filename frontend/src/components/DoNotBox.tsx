import { Ban } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { DoNot } from "../api/client";
import { PendingLabel } from "./PendingLabel";

export function DoNotBox({ items }: { items: DoNot[] }) {
  const { t } = useTranslation();
  if (!items.length) return null;
  return (
    <div className="rounded-card border border-caution-text/20 bg-caution-bg p-4 text-caution-text">
      <p className="flex items-center gap-2 text-note font-semibold uppercase tracking-wide">
        <Ban aria-hidden size={16} />
        {t("do_not")}
      </p>
      <ul className="mt-2 space-y-2">
        {items.map((d) => (
          <li key={d.text} className="text-body">
            <span className="font-semibold">{d.text}</span>
            {d.reason ? <span className="block text-note">{d.reason}</span> : null}
            <PendingLabel show={d.translation_pending} />
          </li>
        ))}
      </ul>
    </div>
  );
}
