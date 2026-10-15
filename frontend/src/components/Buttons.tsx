import type { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode };

export function PrimaryButton({ children, className = "", ...rest }: Props) {
  return (
    <button
      {...rest}
      className={`flex min-h-[56px] w-full items-center justify-center gap-2 rounded-card bg-primary px-4 text-body font-semibold text-surface disabled:opacity-60 focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 ${className}`}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...rest }: Props) {
  return (
    <button
      {...rest}
      className={`flex min-h-[56px] w-full items-center justify-center gap-2 rounded-card border border-border bg-surface px-4 text-body font-semibold text-primary disabled:opacity-60 focus:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 ${className}`}
    >
      {children}
    </button>
  );
}
