import { Activity, Bug, Flame, HeartPulse, UserX } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { PrimaryButton } from "../components/Buttons";

const TILES = [
  { key: "unresponsive", icon: UserX },
  { key: "heart_attack", icon: HeartPulse },
  { key: "choking", icon: Activity },
  { key: "bites", icon: Bug },
  { key: "burns", icon: Flame },
] as const;

export function Home({ onSubmit, onAbout, busy }: { onSubmit: (text: string) => void; onAbout: () => void; busy: boolean }) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  return (
    <div className="flex flex-col gap-6">
      <form
        className="flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) onSubmit(text.trim());
        }}
      >
        <label htmlFor="what" className="text-step font-semibold text-text">
          {t("what_happened")}
        </label>
        <textarea
          id="what"
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("own_words")}
          className="w-full resize-none rounded-card border border-border bg-surface p-4 text-body text-text placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/20"
        />
        <PrimaryButton type="submit" disabled={busy || !text.trim()}>
          {busy ? t("loading") : t("continue")}
        </PrimaryButton>
      </form>

      <section>
        <h2 className="mb-3 text-note font-semibold text-text-muted">{t("or_choose")}</h2>
        <div className="grid grid-cols-2 gap-3">
          {TILES.map(({ key, icon: Icon }, i) => (
            <button
              key={key}
              disabled={busy}
              onClick={() => onSubmit(t(`tile_text_${key}`))}
              className={`flex min-h-[96px] flex-col items-center justify-center gap-2 rounded-card border border-border bg-surface p-4 text-body font-semibold text-text hover:bg-primary-soft focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 ${
                i === TILES.length - 1 ? "col-span-2" : ""
              }`}
            >
              <Icon aria-hidden size={30} strokeWidth={1.6} className="text-primary" />
              {t(`tile_${key}`)}
            </button>
          ))}
        </div>
      </section>

      <footer className="border-t border-border pt-4 text-note text-text-muted">
        <p>{t("disclaimer")}</p>
        <p className="mt-1">
          IFRC 2025 · AHA/Red Cross 2024 · AHA BLS 2025 · ILCOR 2025 · NAPSE ·{" "}
          <button onClick={onAbout} className="text-primary underline">
            {t("about_link")}
          </button>
        </p>
      </footer>
    </div>
  );
}
