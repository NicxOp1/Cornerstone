"use client";

import { cn } from "@/lib/utils/cn";

interface SegmentOption<T extends string> {
  label: string;
  value: T;
}

interface SegmentToggleProps<T extends string> {
  options: Array<SegmentOption<T>>;
  value: T;
  onChange: (value: T) => void;
}

export function SegmentToggle<T extends string>({
  options,
  value,
  onChange
}: SegmentToggleProps<T>) {
  return (
    <div className="inline-flex rounded-full border border-line bg-muted/80 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      {options.map((option) => {
        const active = option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
              active
                ? "bg-[linear-gradient(135deg,rgba(255,248,194,0.98),rgba(245,224,0,0.98))] text-accent-ink shadow-[0_10px_28px_rgba(245,224,0,0.18)]"
                : "text-ink-soft hover:bg-white/5 hover:text-ink"
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
