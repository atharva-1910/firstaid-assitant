import { Check, Copy, Share2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { PendingLabel } from "../components/PendingLabel";

export function Summary({ lines, pending, onStartOver }: { lines: string[]; pending: boolean; onStartOver: () => void }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const text = lines.join("\n");
  const canShare = typeof navigator !== "undefined" && "share" in navigator;
  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-step font-semibold text-text">{t("handover")}</h1>
      <div className="rounded-card border border-border bg-surface p-4">
        <ul className="space-y-2">
          {lines.map((l) => (
            <li key={l} className="text-body text-text">
              {l}
            </li>
          ))}
        </ul>
        <PendingLabel show={pending} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <SecondaryButton
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(text);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            } catch {
              /* clipboard blocked */
            }
          }}
        >
          {copied ? <Check aria-hidden size={20} className="text-success" /> : <Copy aria-hidden size={20} />}
          {copied ? t("copied") : t("copy")}
        </SecondaryButton>
        <SecondaryButton disabled={!canShare} onClick={() => canShare && navigator.share({ text }).catch(() => undefined)}>
          <Share2 aria-hidden size={20} />
          {t("share")}
        </SecondaryButton>
      </div>
      <p className="text-center text-note text-text-muted">{t("reassure")}</p>
      <PrimaryButton onClick={onStartOver}>{t("start_over")}</PrimaryButton>
    </div>
  );
}
