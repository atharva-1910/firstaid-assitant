import { Phone } from "lucide-react";
import { useTranslation } from "react-i18next";

// The only component (with EmergencyBanner) allowed to use the emergency red (Section 14.1).
export function Call112Button({ variant = "pill" }: { variant?: "pill" | "large" }) {
  const { t } = useTranslation();
  if (variant === "large") {
    return (
      <a
        href="tel:112"
        className="flex min-h-[64px] w-full items-center justify-center gap-3 rounded-card bg-emergency px-4 text-step font-semibold text-surface shadow-sm focus:outline-none focus-visible:ring-4 focus-visible:ring-emergency/40"
      >
        <Phone aria-hidden size={26} />
        {t("call_112_now")}
      </a>
    );
  }
  return (
    <a
      href="tel:112"
      className="inline-flex min-h-[44px] shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full bg-emergency px-3 text-note font-semibold text-surface focus:outline-none focus-visible:ring-4 focus-visible:ring-emergency/40"
      aria-label={t("call_112")}
    >
      <Phone aria-hidden size={16} />
      <span>{t("call_112")}</span>
    </a>
  );
}
