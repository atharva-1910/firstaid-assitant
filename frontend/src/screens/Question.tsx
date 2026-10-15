import { useTranslation } from "react-i18next";

import type { Question as Q } from "../api/client";
import { AnswerButtons } from "../components/AnswerButtons";
import { PendingLabel } from "../components/PendingLabel";

export function Question({ question, onAnswer, busy }: { question: Q; onAnswer: (id: string) => void; busy: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="text-question font-semibold text-text">{question.text}</p>
        <PendingLabel show={question.translation_pending} />
        <p className="mt-1 text-note text-text-muted">{t("question_hint")}</p>
      </div>
      <AnswerButtons question={question} onAnswer={onAnswer} disabled={busy} />
    </div>
  );
}
