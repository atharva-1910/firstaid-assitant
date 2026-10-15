import type { Question } from "../api/client";
import { PendingLabel } from "./PendingLabel";

export function AnswerButtons({ question, onAnswer, disabled }: { question: Question; onAnswer: (id: string) => void; disabled?: boolean }) {
  return (
    <div className="flex flex-col gap-3">
      {question.options.slice(0, 5).map((o) => (
        <button
          key={o.id}
          disabled={disabled}
          onClick={() => onAnswer(o.id)}
          className="min-h-[56px] w-full rounded-card border border-border bg-surface px-4 py-3 text-left text-body font-semibold text-text hover:bg-primary-soft focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 disabled:opacity-60"
        >
          {o.label}
          <PendingLabel show={o.translation_pending} />
        </button>
      ))}
    </div>
  );
}
