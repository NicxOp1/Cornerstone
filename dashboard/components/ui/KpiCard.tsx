import type { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { Sparkline } from "@/components/ui/Sparkline";
import { cn } from "@/lib/utils/cn";

type DeltaTone = "bad" | "good" | "neutral";
type SparkTone = "accent" | "bad" | "good" | "ink";

const deltaToneClasses: Record<DeltaTone, string> = {
  bad: "border border-bad/20 bg-bad-soft text-bad",
  good: "border border-good/20 bg-good-soft text-good",
  neutral: "border border-white/6 bg-muted text-ink-soft"
};

const iconToneClasses: Record<SparkTone, string> = {
  accent: "border border-accent/18 bg-accent/14 text-accent",
  bad: "border border-bad/20 bg-bad-soft/80 text-bad",
  good: "border border-good/20 bg-good-soft/80 text-good",
  ink: "border border-line-strong/80 bg-navy/30 text-[rgb(var(--heat))]"
};

const sparkSurfaceClasses: Record<SparkTone, string> = {
  accent: "border border-accent/16 bg-accent/8",
  bad: "border border-bad/16 bg-bad-soft/60",
  good: "border border-good/16 bg-good-soft/60",
  ink: "border border-line/70 bg-muted/90"
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
    <Card className="group flex h-full flex-col gap-5 overflow-hidden transition duration-200 will-change-transform hover:-translate-y-1 hover:border-accent/25 hover:shadow-[0_26px_64px_rgba(2,6,20,0.30)]">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-ink-soft">
            {label}
          </p>
          <p className="text-3xl font-semibold tracking-tight text-ink tabular-nums md:text-[2rem]">
            {value}
          </p>
        </div>
        <div
          className={cn(
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-[18px] transition-transform duration-200 group-hover:scale-105",
            iconToneClasses[sparkTone]
          )}
        >
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
        <div
          className={cn(
            "h-11 w-28 rounded-[18px] px-2.5 py-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
            sparkSurfaceClasses[sparkTone]
          )}
        >
          <Sparkline points={trend} tone={sparkTone} />
        </div>
      </div>
    </Card>
  );
}
