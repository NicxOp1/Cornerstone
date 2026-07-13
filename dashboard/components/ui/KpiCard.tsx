import type { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { Sparkline } from "@/components/ui/Sparkline";
import { cn } from "@/lib/utils/cn";

type DeltaTone = "bad" | "good" | "neutral";
type SparkTone = "accent" | "bad" | "good" | "ink";

const deltaToneClasses: Record<DeltaTone, string> = {
  bad: "bg-bad-soft text-bad",
  good: "bg-good-soft text-good",
  neutral: "bg-muted text-ink-soft"
};

interface KpiCardProps {
  label: string;
  value: string;
  footnote: string;
  deltaLabel: string;
  deltaTone?: DeltaTone;
  trend: number[];
  sparkTone?: SparkTone;
  icon: ReactNode;
}

export function KpiCard({
  label,
  value,
  footnote,
  deltaLabel,
  deltaTone = "neutral",
  trend,
  sparkTone = "accent",
  icon
}: KpiCardProps) {
  return (
    <Card className="flex h-full flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-ink-soft">
            {label}
          </p>
          <p className="text-3xl font-semibold tracking-tight text-ink tabular-nums md:text-[2rem]">
            {value}
          </p>
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-muted text-navy">
          {icon}
        </div>
      </div>

      <p className="text-sm leading-6 text-ink-soft">{footnote}</p>

      <div className="mt-auto flex items-end justify-between gap-4 border-t border-line/70 pt-4">
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]",
            deltaToneClasses[deltaTone]
          )}
        >
          {deltaLabel}
        </span>
        <div className="h-10 w-24 rounded-2xl bg-muted/70 px-2 py-2">
          <Sparkline points={trend} tone={sparkTone} />
        </div>
      </div>
    </Card>
  );
}
