"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { RangeOption } from "@/lib/metrics";
import { cn } from "@/lib/utils/cn";

const OPTIONS: Array<{ label: string; value: RangeOption }> = [
  { label: "7 days", value: "7" },
  { label: "30 days", value: "30" },
  { label: "All", value: "all" }
];

export function DateRangeSelector({ value }: { value: RangeOption }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function select(next: RangeOption) {
    const params = new URLSearchParams(searchParams.toString());

    if (next === "30") {
      params.delete("range");
    } else {
      params.set("range", next);
    }

    const query = params.toString();
    router.push(query ? `${pathname}?${query}` : pathname);
  }

  return (
    <div className="inline-flex rounded-full border border-line/80 bg-muted/60 p-1">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => select(option.value)}
          aria-pressed={value === option.value}
          className={cn(
            "rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors",
            value === option.value ? "bg-card text-ink shadow-sm" : "text-ink-soft hover:text-ink"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
