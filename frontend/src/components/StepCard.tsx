import type { Step } from "../api/client";
import { PendingLabel } from "./PendingLabel";

export function StepCard({ step }: { step: Step }) {
  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <p className="text-step font-semibold text-text" data-testid="step-text">
        {step.text}
      </p>
      <PendingLabel show={step.translation_pending} />
    </div>
  );
}
