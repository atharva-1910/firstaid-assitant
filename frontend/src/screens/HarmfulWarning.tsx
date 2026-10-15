import { Ban } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { HarmfulAction } from "../api/client";
import { PrimaryButton } from "../components/Buttons";
import { PendingLabel } from "../components/PendingLabel";
import { SOURCES } from "../sources";

export function HarmfulWarning({ harmful, onContinue }: { harmful: HarmfulAction; onContinue: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-card border border-caution-text/20 bg-caution-bg p-4 text-caution-text">
        <p className="flex items-center gap-2 text-question font-semibold">
          <Ban aria-hidden size={22} />
          {t("do_not")}
        </p>
        <p className="mt-3 text-step font-semibold">{harmful.action}</p>
        <p className="mt-2 text-body">{harmful.reason}</p>
        <PendingLabel show={harmful.translation_pending} />
        {harmful.source && SOURCES[harmful.source] ? <p className="mt-2 text-note">{SOURCES[harmful.source].short}</p> : null}
      </div>
      <PrimaryButton onClick={onContinue}>{t("harmful_continue")}</PrimaryButton>
    </div>
  );
}
