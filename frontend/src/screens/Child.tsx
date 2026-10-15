import { useTranslation } from "react-i18next";

import { SecondaryButton } from "../components/Buttons";
import { Call112Button } from "../components/Call112Button";

export function Child({ onStartOver }: { onStartOver: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-step font-semibold text-text">{t("child_title")}</h1>
      <Call112Button variant="large" />
      <p className="text-body text-text">{t("child_text")}</p>
      <SecondaryButton onClick={onStartOver}>{t("start_over")}</SecondaryButton>
    </div>
  );
}
