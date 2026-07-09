import { AreaTrend } from "@/components/charts/AreaTrend";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { KpiCard } from "@/components/ui/KpiCard";
import { TabHeader } from "@/components/ui/TabHeader";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { dayBuckets, kpiDelta, previousWindow } from "@/lib/kpi";
import {
  averageCostPerMinuteCents,
  costPerCallCents,
  costPerDay,
  filterByRange,
  monthlyProjectionCents,
  parseRange,
  sumCostCents
} from "@/lib/metrics";
import { formatCompactCost, formatCurrency, formatDayShort, formatNumber, formatRangeEyebrow } from "@/lib/utils/format";

export const dynamic = "force-dynamic";

function CostIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3v18M16 7.5c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.1 2.5 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3" />
    </svg>
  );
}

export default async function CostPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);
  const calls = filterByRange(await getCachedCalls(), range);
  const previous = previousWindow(calls);
  const buckets = dayBuckets(calls);
  const daily = costPerDay(calls);
  const rangeLabel = daily.length > 0 ? formatRangeEyebrow(daily[0].date, daily[daily.length - 1].date) : "";

  const costPerMinDelta = kpiDelta(calls, previous, averageCostPerMinuteCents, false);
  const costPerCallDelta = kpiDelta(calls, previous, costPerCallCents, false);

  const kpis = [
    {
      label: "Cost per minute",
      value: formatCompactCost(averageCostPerMinuteCents(calls)),
      footnote: `${formatCurrency(sumCostCents(calls))} total spend this window`,
      deltaLabel: costPerMinDelta.label,
      deltaTone: costPerMinDelta.tone,
      trend: buckets.map((bucket) => averageCostPerMinuteCents(bucket)),
      sparkTone: "ink" as const
    },
    {
      label: "Cost per call",
      value: formatCompactCost(costPerCallCents(calls)),
      footnote: `Across ${formatNumber(calls.length)} calls`,
      deltaLabel: costPerCallDelta.label,
      deltaTone: costPerCallDelta.tone,
      trend: buckets.map((bucket) => costPerCallCents(bucket)),
      sparkTone: "ink" as const
    },
    {
      label: "Total spend",
      value: formatCurrency(sumCostCents(calls)),
      footnote: "Full spend for the selected window",
      deltaLabel: "This window",
      deltaTone: "neutral" as const,
      trend: buckets.map((bucket) => sumCostCents(bucket)),
      sparkTone: "accent" as const
    },
    {
      label: "Projected / month",
      value: formatCurrency(monthlyProjectionCents(calls)),
      footnote: "Linear estimate from the daily pace",
      deltaLabel: "Estimate",
      deltaTone: "neutral" as const,
      trend: buckets.map((bucket) => sumCostCents(bucket)),
      sparkTone: "accent" as const
    }
  ];

  return (
    <div className="space-y-6">
      <TabHeader
        eyebrow={rangeLabel}
        title="Cost"
        description="What Harmony costs to run, with daily spend shown on a clearer money-by-day trend."
        range={range}
      />

      {calls.length === 0 ? (
        <EmptyState
          title="No calls in this window"
          description="Widen the date range or wait for the next sync to see spend."
        />
      ) : (
        <>
          <section className="grid grid-cols-1 gap-4 xl:grid-cols-4">
            {kpis.map((kpi) => (
              <KpiCard key={kpi.label} {...kpi} icon={<CostIcon />} />
            ))}
          </section>

          <Card className="space-y-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Spend</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Cost per day</h2>
              <p className="mt-2 text-sm text-ink-soft">
                X-axis shows the day. Y-axis shows total USD spent on that day.
              </p>
            </div>
            <AreaTrend
              data={daily.map((point) => ({
                date: point.date,
                label: formatDayShort(point.date),
                value: point.cents
              }))}
              format="currency"
              strokeVar="accent"
              fillVar="accent"
            />
          </Card>
        </>
      )}
    </div>
  );
}
