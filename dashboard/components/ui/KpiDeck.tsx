"use client";

import { useState, type ReactNode } from "react";
import { AreaTrend } from "@/components/charts/AreaTrend";
import { EmptyState } from "@/components/ui/EmptyState";
import { KpiCard } from "@/components/ui/KpiCard";
import { Modal } from "@/components/ui/Modal";
import { cn } from "@/lib/utils/cn";
import { formatDayShort } from "@/lib/utils/format";

type DeltaTone = "bad" | "good" | "neutral";
type SparkTone = "accent" | "bad" | "good" | "ink";
export type KpiChartFormat = "currency" | "duration" | "number" | "percent";

export interface KpiDeckItem {
  label: string;
  value: string;
  footnote: string;
  deltaLabel: string;
  deltaTone: DeltaTone;
  trend: number[];
  sparkTone: SparkTone;
  icon: ReactNode;
  chartFormat: KpiChartFormat;
}

interface KpiDeckProps {
  items: KpiDeckItem[];
  /** Días (YYYY-MM-DD) alineados por índice con `trend` de cada KPI, para el eje X del modal. */
  trendDays: string[];
  gridClassName?: string;
}

const SPARK_STROKE_VAR: Record<SparkTone, string> = {
  accent: "accent",
  bad: "bad",
  good: "good",
  ink: "navy-2"
};

const deltaBadgeClasses: Record<DeltaTone, string> = {
  bad: "border border-bad/20 bg-bad-soft text-bad",
  good: "border border-good/20 bg-good-soft text-good",
  neutral: "border border-white/6 bg-muted text-ink-soft"
};

export function KpiDeck({ items, trendDays, gridClassName }: KpiDeckProps) {
  const [active, setActive] = useState<number | null>(null);
  const open = active !== null ? items[active] : null;

  const points =
    open?.trend.map((value, index) => ({
      date: trendDays[index] ?? String(index),
      label: trendDays[index] ? formatDayShort(trendDays[index]) : "",
      value
    })) ?? [];

  return (
    <>
      <section className={cn("grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4", gridClassName)}>
        {items.map((item, index) => {
          const { chartFormat: _chartFormat, ...cardProps } = item;

          return <KpiCard key={item.label} {...cardProps} onShowChart={() => setActive(index)} />;
        })}
      </section>

      <Modal
        open={open !== null}
        onClose={() => setActive(null)}
        title={open?.label ?? ""}
        subtitle={open?.footnote}
      >
        {open ? (
          <div className="space-y-5">
            <div className="flex flex-wrap items-end gap-4">
              <p className="text-4xl font-semibold tracking-tight text-ink tabular-nums">{open.value}</p>
              <span
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]",
                  deltaBadgeClasses[open.deltaTone]
                )}
              >
                {open.deltaLabel}
              </span>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
                Daily breakdown
              </p>
              {points.length === 0 ? (
                <EmptyState
                  title="No data in this window"
                  description="Once calls are synced, the per-day breakdown will appear here."
                />
              ) : (
                <AreaTrend
                  data={points}
                  format={open.chartFormat}
                  strokeVar={SPARK_STROKE_VAR[open.sparkTone]}
                  fillVar={SPARK_STROKE_VAR[open.sparkTone]}
                />
              )}
            </div>
          </div>
        ) : null}
      </Modal>
    </>
  );
}
