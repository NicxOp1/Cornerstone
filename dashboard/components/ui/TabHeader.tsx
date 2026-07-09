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
    <header className="relative overflow-hidden rounded-[34px] border border-line/70 bg-card/90 p-6 shadow-panel md:flex md:items-end md:justify-between md:p-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(245,224,0,0.15),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)]" />
      <div className="relative space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent/75">
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
      <div className="relative mt-5 md:mt-0">
        <DateRangeSelector value={range} />
      </div>
    </header>
  );
}
