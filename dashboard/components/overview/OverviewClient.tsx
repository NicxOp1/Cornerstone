"use client";

import { useMemo, useState } from "react";
import { AreaTrend } from "@/components/charts/AreaTrend";
import { Donut } from "@/components/charts/Donut";
import { Heatmap } from "@/components/charts/Heatmap";
import { StackedBars } from "@/components/charts/StackedBars";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { KpiCard } from "@/components/ui/KpiCard";
import { DateRangeSelector } from "@/components/ui/DateRangeSelector";
import { SegmentToggle } from "@/components/ui/SegmentToggle";
import type { RangeOption } from "@/lib/metrics";
import { formatNumber } from "@/lib/utils/format";

type DeltaTone = "bad" | "good" | "neutral";
type KpiIcon = "bookings" | "cost" | "duration" | "success";
type SparkTone = "accent" | "bad" | "good" | "ink";

interface OverviewKpi {
  deltaLabel: string;
  deltaTone: DeltaTone;
  footnote: string;
  icon: KpiIcon;
  label: string;
  sparkTone: SparkTone;
  trend: number[];
  value: string;
}

interface OverviewTrendPoint {
  date: string;
  label: string;
  value: number;
}

interface OverviewSentimentSegment {
  color: "neg" | "neu" | "pos" | "unk";
  label: string;
  value: number;
}

interface OverviewActivityPoint {
  date: string;
  label: string;
  fail: number;
  success: number;
  total: number;
}

interface OverviewClientProps {
  activityBars: OverviewActivityPoint[];
  activityHeatmap: number[][];
  dailyTrend: OverviewTrendPoint[];
  kpis: OverviewKpi[];
  range: RangeOption;
  rangeLabel: string;
  sentimentSegments: OverviewSentimentSegment[];
  totalCalls: number;
}

function iconFor(name: KpiIcon) {
  switch (name) {
    case "bookings":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M7 3v4M17 3v4M4 9h16M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
          <path d="m9 14 2 2 4-5" />
        </svg>
      );
    case "success":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M4 12h4l2-5 4 10 2-5h4" />
        </svg>
      );
    case "duration":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v4l3 2" />
        </svg>
      );
    case "cost":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 3v18M16 7.5c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.1 2.5 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3" />
        </svg>
      );
    default:
      return null;
  }
}

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) {
    return "Good morning";
  }

  if (hour < 18) {
    return "Good afternoon";
  }

  return "Good evening";
}

export function OverviewClient({
  activityBars,
  activityHeatmap,
  dailyTrend,
  kpis,
  range,
  rangeLabel,
  sentimentSegments,
  totalCalls
}: OverviewClientProps) {
  const [mode, setMode] = useState<"day" | "hour">("day");
  const greeting = useMemo(() => getGreeting(), []);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-5 rounded-[32px] border border-line/70 bg-card/80 p-6 shadow-panel md:flex-row md:items-end md:justify-between md:p-8">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
            {rangeLabel || "SYNC PENDING"}
          </p>
          <div>
            <h1 className="font-display text-4xl leading-none tracking-tight text-ink md:text-6xl">
              {greeting}
            </h1>
            <p className="mt-3 text-sm leading-6 text-ink-soft md:text-base">
              {formatNumber(totalCalls)} calls tracked in this window.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <DateRangeSelector value={range} />
          <button
            type="button"
            className="inline-flex h-11 items-center justify-center rounded-full border border-navy/10 bg-navy px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-navy-2"
          >
            Export report
          </button>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <KpiCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            footnote={kpi.footnote}
            deltaLabel={kpi.deltaLabel}
            deltaTone={kpi.deltaTone}
            trend={kpi.trend}
            sparkTone={kpi.sparkTone}
            icon={iconFor(kpi.icon)}
          />
        ))}
      </section>

      <Card className="space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
              Activity
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Call activity</h2>
          </div>
          <SegmentToggle
            options={[
              { label: "Day", value: "day" },
              { label: "Hour", value: "hour" }
            ]}
            value={mode}
            onChange={setMode}
          />
        </div>
        {activityBars.length === 0 ? (
          <EmptyState
            title="No call activity yet"
            description="Once calls are synced, daily and hourly activity will appear here."
          />
        ) : mode === "day" ? (
          <StackedBars data={activityBars} />
        ) : (
          <Heatmap matrix={activityHeatmap} />
        )}
      </Card>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_minmax(0,1fr)]">
        <Card className="space-y-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Volume</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Daily trend</h2>
          </div>
          {dailyTrend.length === 0 ? (
            <EmptyState
              title="No daily trend yet"
              description="We need synced calls before the volume trend can be drawn."
            />
          ) : (
            <AreaTrend data={dailyTrend} format="number" />
          )}
        </Card>

        <Card className="space-y-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
              Quality
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Sentiment</h2>
          </div>
          <Donut segments={sentimentSegments} totalLabel="Calls" />
        </Card>
      </section>
    </div>
  );
}
