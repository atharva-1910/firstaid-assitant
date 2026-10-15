import { useTranslation } from "react-i18next";

import type { Urgency } from "../api/client";
import { EmergencyBanner } from "./EmergencyBanner";

export function UrgencyNote({ urgency }: { urgency: Urgency }) {
  const { t } = useTranslation();
  if (urgency === "emergency") return <EmergencyBanner title={t("urgency_emergency")} />;
  return (
    <div className="rounded-card bg-primary-soft p-3 text-body text-text">{t(urgency === "clinic" ? "urgency_clinic" : "urgency_home")}</div>
  );
}
