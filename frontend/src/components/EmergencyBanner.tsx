import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

// Emergency banner: one of the two places red is allowed (Section 14.1).
export function EmergencyBanner({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div role="alert" className="rounded-card border border-emergency/30 bg-emergency-soft p-4 text-text">
      <div className="flex items-start gap-3">
        <AlertTriangle aria-hidden className="mt-1 shrink-0 text-emergency" size={24} />
        <div>
          <p className="text-question font-semibold text-emergency">{title}</p>
          {children ? <div className="mt-1 text-body">{children}</div> : null}
        </div>
      </div>
    </div>
  );
}
