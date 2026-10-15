import { useTranslation } from "react-i18next";

import type { Lang } from "../api/client";
import { LANGUAGES } from "../i18n";
import { Call112Button } from "./Call112Button";

export function Header({ lang, onLang, onHome }: { lang: Lang; onLang: (l: Lang) => void; onHome: () => void }) {
  const { t } = useTranslation();
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-column items-center justify-between gap-2 px-4 py-2">
        <button onClick={onHome} className="min-h-[44px] min-w-0 truncate text-left text-note font-semibold text-primary">
          {t("app_name")}
        </button>
        <div className="flex shrink-0 items-center gap-2">
          <label className="sr-only" htmlFor="lang">
            {t("language")}
          </label>
          <select
            id="lang"
            value={lang}
            onChange={(e) => onLang(e.target.value as Lang)}
            className="min-h-[44px] max-w-[110px] rounded-card border border-border bg-surface px-1.5 text-note text-text"
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
          <Call112Button />
        </div>
      </div>
    </header>
  );
}
