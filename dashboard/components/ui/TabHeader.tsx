import { DateRangeSelector } from "@/components/ui/DateRangeSelector";
import type { RangeOption } from "@/lib/metrics";

interface TabHeaderProps {
  eyebrow: string;
  title: string;
  description?: string;
  range: RangeOption;
}

export function TabHeader({ eyebrow, title, description, range }: TabHeaderProps) {
  return (
    <header className="flex flex-col gap-5 rounded-[32px] border border-line/70 bg-card/80 p-6 shadow-panel md:flex-row md:items-end md:justify-between md:p-8">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
          {eyebrow || "SYNC PENDING"}
        </p>
        <div>
          <h1 className="font-display text-3xl leading-none tracking-tight text-ink md:text-5xl">
            {title}
          </h1>
          {description ? (
            <p className="mt-3 max-w-2xl text-sm leading-6 text-ink-soft md:text-base">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      <DateRangeSelector value={range} />
    </header>
  );
}
