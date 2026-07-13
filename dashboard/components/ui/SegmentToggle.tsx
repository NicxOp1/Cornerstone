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
    <div className="inline-flex rounded-full border border-line bg-muted p-1">
      {options.map((option) => {
        const active = option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
              active ? "bg-card text-ink shadow-sm" : "text-ink-soft hover:text-ink"
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
