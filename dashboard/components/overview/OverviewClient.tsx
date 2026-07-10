"use client";

import { useMemo, useState } from "react";
import { Logo } from "@/components/Logo";
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

const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

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

function getBusiestWindow(matrix: number[][]): string {
  let best = 0;
  let bestDay = 0;
  let bestHour = 0;

  matrix.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      if (value > best) {
        best = value;
        bestDay = rowIndex;
        bestHour = columnIndex;
      }
    });
  });

  if (best === 0) {
    return "Activity snapshot fills in after sync";
  }

  return `${WEEKDAY_LABELS[bestDay]} ${String(bestHour).padStart(2, "0")}:00 is the busiest block`;
}

function getSentimentLeader(segments: OverviewSentimentSegment[]): string {
  const leader = segments.reduce<OverviewSentimentSegment | null>((best, segment) => {
    if (segment.value <= 0) {
      return best;
    }

    if (!best || segment.value > best.value) {
      return segment;
    }

    return best;
  }, null);

  if (!leader) {
    return "Sentiment mix appears once calls are scored";
  }

  return `${leader.label} leads the sentiment mix`;
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
  const busiestWindow = useMemo(() => getBusiestWindow(activityHeatmap), [activityHeatmap]);
  const sentimentLeader = useMemo(() => getSentimentLeader(sentimentSegments), [sentimentSegments]);

  return (
    <div className="space-y-6">
      <header className="animate-rise relative overflow-hidden rounded-[36px] border border-line/70 bg-[linear-gradient(180deg,rgba(8,11,21,0.98),rgba(18,24,43,0.94))] p-6 shadow-panel md:p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(245,224,0,0.2),transparent_30%),radial-gradient(circle_at_left_center,rgba(81,92,191,0.18),transparent_22%)]" />
        <div className="relative flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl space-y-5">
            <span className="inline-flex rounded-full border border-accent/18 bg-accent/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
              {rangeLabel || "Live window"}
            </span>
            <div className="flex justify-center py-1">
              <Logo className="h-24 md:h-28" />
            </div>
            <div>
              <h1 className="font-display text-4xl leading-none tracking-tight text-white md:text-6xl">
                {greeting}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-white/70 md:text-base">
                {formatNumber(totalCalls)} calls tracked in this window. {busiestWindow}. {sentimentLeader}.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4 xl:items-end">
            <div className="flex flex-wrap items-center gap-3">
              <DateRangeSelector value={range} />
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:w-[420px]">
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/52">
                  Calls tracked
                </p>
                <p className="mt-3 text-2xl font-semibold text-white">{formatNumber(totalCalls)}</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/52">
                  Best read
                </p>
                <p className="mt-3 text-sm font-semibold leading-6 text-white">{sentimentLeader}</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/52">
                  Activity
                </p>
                <p className="mt-3 text-sm font-semibold leading-6 text-white">{busiestWindow}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section
        className="animate-rise grid grid-cols-1 gap-4 xl:grid-cols-4"
        style={{ animationDelay: "80ms" }}
      >
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

      <Card className="animate-rise space-y-6" style={{ animationDelay: "160ms" }}>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent/75">Activity</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Call activity</h2>
            <p className="mt-2 text-sm text-ink-soft">
              {mode === "day"
                ? "Resolved versus unresolved volume by day."
                : "Weekly concentration by hour, from quiet blocks to busy spikes."}
            </p>
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

      <section
        className="animate-rise grid gap-6 xl:grid-cols-[1.35fr_minmax(0,1fr)]"
        style={{ animationDelay: "240ms" }}
      >
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
            <AreaTrend data={dailyTrend} format="number" strokeVar="navy-2" fillVar="navy-2" />
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
