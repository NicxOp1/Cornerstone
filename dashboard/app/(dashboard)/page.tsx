import { OverviewClient } from "@/components/overview/OverviewClient";
import { getCachedCalls } from "@/lib/data/cached-repository";
import {
  averageCostPerMinuteCents,
  averageDurationSeconds,
  bookingEffectivenessBreakdown,
  dailySeries,
  filterByRange,
  hourWeekdayMatrix,
  parseRange,
  periodDelta,
  sentimentBreakdown,
  successRate,
  sumCostCents
} from "@/lib/metrics";
import type { Call } from "@/lib/types/call";
import {
  addUtcDays,
  formatCompactCost,
  formatCurrency,
  formatDayShort,
  formatDuration,
  formatNumber,
  formatPercent,
  formatRangeEyebrow,
  inclusiveDaySpan,
  parseDay
} from "@/lib/utils/format";

export const dynamic = "force-dynamic";

interface DayBucket {
  date: string;
  calls: Call[];
}

function buildDayBuckets(calls: Call[]): DayBucket[] {
  const buckets = new Map<string, Call[]>();

  for (const call of calls) {
    if (!call.day) {
      continue;
    }

    const existing = buckets.get(call.day) ?? [];
    existing.push(call);
    buckets.set(call.day, existing);
  }

  return [...buckets.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, dayCalls]) => ({ date, calls: dayCalls }));
}

function buildPreviousWindow(calls: Call[]): Call[] {
  const parsedDays = calls
    .map((call) => parseDay(call.day))
    .filter((date): date is Date => date !== null)
    .sort((left, right) => left.getTime() - right.getTime());

  if (parsedDays.length === 0) {
    return [];
  }

  const start = parsedDays[0];
  const end = parsedDays[parsedDays.length - 1];
  const span = inclusiveDaySpan(start, end);
  const previousEnd = addUtcDays(start, -1);
  const previousStart = addUtcDays(previousEnd, -(span - 1));

  return calls.filter((call) => {
    const callDate = parseDay(call.day);

    if (!callDate) {
      return false;
    }

    return callDate >= previousStart && callDate <= previousEnd;
  });
}

function buildDeltaLabel(change: number | null, higherIsBetter: boolean | null) {
  if (change === null) {
    return { label: "First window", tone: "neutral" as const };
  }

  if (change === 0) {
    return { label: "Flat vs prior", tone: "neutral" as const };
  }

  const positive = change > 0;
  const tone =
    higherIsBetter === null
      ? ("neutral" as const)
      : positive === higherIsBetter
        ? ("good" as const)
        : ("bad" as const);

  return {
    label: `${positive ? "+" : ""}${change.toFixed(1)}% vs prior`,
    tone
  };
}

export default async function OverviewPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);
  const calls = filterByRange(await getCachedCalls(), range);
  const previousWindow = buildPreviousWindow(calls);
  const bookings = bookingEffectivenessBreakdown(calls);
  const sentiments = sentimentBreakdown(calls);
  const daily = dailySeries(calls);
  const dayBuckets = buildDayBuckets(calls);
  const successTotal = calls.filter((call) => call.callSuccessful === true).length;
  const totalCost = sumCostCents(calls);
  const rangeLabel =
    daily.length > 0 ? formatRangeEyebrow(daily[0].date, daily[daily.length - 1].date) : "";

  const bookingDelta = buildDeltaLabel(
    periodDelta(calls, previousWindow, (entries) => bookingEffectivenessBreakdown(entries).confirmed)
      .changePercent,
    true
  );
  const successDelta = buildDeltaLabel(
    periodDelta(calls, previousWindow, successRate).changePercent,
    true
  );
  const durationDelta = buildDeltaLabel(
    periodDelta(calls, previousWindow, averageDurationSeconds).changePercent,
    null
  );
  const costDelta = buildDeltaLabel(
    periodDelta(calls, previousWindow, averageCostPerMinuteCents).changePercent,
    false
  );

  const kpis = [
    {
      label: "Bookings confirmed",
      value: formatNumber(bookings.confirmed),
      footnote: `${formatPercent(bookings.confirmedRate)} of actionable calls`,
      deltaLabel: bookingDelta.label,
      deltaTone: bookingDelta.tone,
      trend: dayBuckets.map(
        (bucket) =>
          bucket.calls.filter((call) => call.bookingEffectiveness === "confirmed").length
      ),
      sparkTone: "accent" as const,
      icon: "bookings" as const
    },
    {
      label: "Success rate",
      value: formatPercent(successRate(calls)),
      footnote: `${formatNumber(successTotal)} successful calls`,
      deltaLabel: successDelta.label,
      deltaTone: successDelta.tone,
      trend: dayBuckets.map((bucket) => successRate(bucket.calls)),
      sparkTone: "good" as const,
      icon: "success" as const
    },
    {
      label: "Avg. duration",
      value: formatDuration(averageDurationSeconds(calls)),
      footnote: `Across ${formatNumber(calls.length)} synced calls`,
      deltaLabel: durationDelta.label,
      deltaTone: durationDelta.tone,
      trend: dayBuckets.map((bucket) => averageDurationSeconds(bucket.calls)),
      sparkTone: "ink" as const,
      icon: "duration" as const
    },
    {
      label: "Cost per minute",
      value: formatCompactCost(averageCostPerMinuteCents(calls)),
      footnote: `${formatCurrency(totalCost)} total period cost`,
      deltaLabel: costDelta.label,
      deltaTone: costDelta.tone,
      trend: dayBuckets.map((bucket) => averageCostPerMinuteCents(bucket.calls)),
      sparkTone: "bad" as const,
      icon: "cost" as const
    }
  ];

  return (
    <OverviewClient
      range={range}
      rangeLabel={rangeLabel}
      totalCalls={calls.length}
      kpis={kpis}
      activityBars={daily.map((point) => ({
        date: point.date,
        label: formatDayShort(point.date),
        success: point.success,
        fail: point.fail,
        total: point.total
      }))}
      activityHeatmap={hourWeekdayMatrix(calls)}
      dailyTrend={daily.map((point) => ({
        date: point.date,
        label: formatDayShort(point.date),
        value: point.total
      }))}
      sentimentSegments={[
        { label: "Positive", value: sentiments.Positive ?? 0, color: "pos" },
        { label: "Neutral", value: sentiments.Neutral ?? 0, color: "neu" },
        { label: "Negative", value: sentiments.Negative ?? 0, color: "neg" },
        { label: "No data", value: sentiments.Unknown ?? 0, color: "unk" }
      ]}
    />
  );
}
