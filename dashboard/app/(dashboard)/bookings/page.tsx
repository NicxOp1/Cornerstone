import Link from "next/link";
import { Bars } from "@/components/charts/Bars";
import { FunnelBars } from "@/components/charts/FunnelBars";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { KpiDeck } from "@/components/ui/KpiDeck";
import { StatusChip } from "@/components/ui/StatusChip";
import { TabHeader } from "@/components/ui/TabHeader";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { dayBuckets, kpiDelta, previousWindow } from "@/lib/kpi";
import {
  bookingFunnel,
  bookingsByAction,
  bookingsPerDay,
  confirmedBookings,
  filterByRange,
  parseRange
} from "@/lib/metrics";
import { formatDayShort, formatNumber, formatPercent, formatRangeEyebrow } from "@/lib/utils/format";

export const dynamic = "force-dynamic";

const ACTION_LABELS: Record<string, string> = {
  schedule: "Schedule",
  reschedule: "Reschedule",
  cancel: "Cancel",
  new_customer: "New customer"
};

function labelAction(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function BookingIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 3v4M17 3v4M4 9h16M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm3 9 2 2 4-5" />
    </svg>
  );
}

export default async function BookingsPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);
  const calls = filterByRange(await getCachedCalls(), range);
  const previous = previousWindow(calls);
  const buckets = dayBuckets(calls);
  const funnel = bookingFunnel(calls);
  const perDay = bookingsPerDay(calls);
  const byAction = bookingsByAction(calls);
  const recent = confirmedBookings(calls).slice(0, 8);
  const rangeLabel = perDay.length > 0 ? formatRangeEyebrow(perDay[0].date, perDay[perDay.length - 1].date) : "";

  const bookingRate = funnel.valid > 0 ? Math.round((funnel.confirmed / funnel.valid) * 1000) / 10 : 0;
  const activeDays = buckets.filter((bucket) =>
    bucket.some((call) => call.bookingEffectiveness === "confirmed")
  ).length;
  const avgPerDay = activeDays > 0 ? Math.round((funnel.confirmed / activeDays) * 10) / 10 : 0;
  const busiest = byAction[0] ? labelAction(byAction[0].action) : "—";

  const confirmedDelta = kpiDelta(calls, previous, (entries) => bookingFunnel(entries).confirmed, true);

  const trendDays = buckets.map((bucket) => bucket[0]?.day ?? "");

  const kpis = [
    {
      label: "Bookings confirmed",
      value: formatNumber(funnel.confirmed),
      footnote: `${formatPercent(bookingRate)} of valid calls booked`,
      deltaLabel: confirmedDelta.label,
      deltaTone: confirmedDelta.tone,
      trend: buckets.map((bucket) => bucket.filter((call) => call.bookingEffectiveness === "confirmed").length),
      sparkTone: "good" as const,
      icon: <BookingIcon />,
      chartFormat: "number" as const
    },
    {
      label: "Booking rate",
      value: formatPercent(bookingRate),
      footnote: `${formatNumber(funnel.confirmed)} of ${formatNumber(funnel.valid)} valid calls`,
      deltaLabel: "Of valid calls",
      deltaTone: "neutral" as const,
      trend: buckets.map((bucket) => bookingFunnel(bucket).confirmed),
      sparkTone: "accent" as const,
      icon: <BookingIcon />,
      chartFormat: "number" as const
    },
    {
      label: "Avg. bookings / day",
      value: String(avgPerDay),
      footnote: `Across ${formatNumber(activeDays)} active days`,
      deltaLabel: "This window",
      deltaTone: "neutral" as const,
      trend: buckets.map((bucket) => bookingFunnel(bucket).confirmed),
      sparkTone: "ink" as const,
      icon: <BookingIcon />,
      chartFormat: "number" as const
    },
    {
      label: "Busiest action",
      value: busiest,
      footnote: byAction[0] ? `${formatNumber(byAction[0].count)} times this window` : "No actions yet",
      deltaLabel: "Most frequent",
      deltaTone: "neutral" as const,
      trend: buckets.map((bucket) => bookingFunnel(bucket).confirmed),
      sparkTone: "accent" as const,
      icon: <BookingIcon />,
      chartFormat: "number" as const
    }
  ];

  return (
    <div className="space-y-6">
      <TabHeader
        eyebrow={rangeLabel}
        title="Bookings"
        description="Where calls turn into booked work — the confirmation funnel and what got scheduled."
        range={range}
      />

      {calls.length === 0 ? (
        <EmptyState
          title="No calls in this window"
          description="Widen the date range or wait for the next sync to see bookings."
        />
      ) : (
        <>
          <KpiDeck items={kpis} trendDays={trendDays} />

          <Card className="space-y-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Conversion</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Booking funnel</h2>
            </div>
            <FunnelBars
              stages={[
                { label: "Total calls", value: funnel.total },
                { label: "Valid (no spam)", value: funnel.valid },
                { label: "Confirmed bookings", value: funnel.confirmed }
              ]}
            />
          </Card>

          <section className="grid gap-6 xl:grid-cols-2">
            <Card className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Volume</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Bookings per day</h2>
              </div>
              <Bars
                data={perDay.map((point) => ({
                  label: formatDayShort(point.date),
                  values: { confirmed: point.confirmed }
                }))}
                series={[{ key: "confirmed", label: "Bookings", colorVar: "good" }]}
              />
            </Card>

            <Card className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Breakdown</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Bookings by action</h2>
              </div>
              {byAction.length === 0 ? (
                <EmptyState
                  title="No booking actions yet"
                  description="Action type is captured from the latest Harmony version onward."
                />
              ) : (
                <Bars
                  data={byAction.map((entry) => ({ label: labelAction(entry.action), values: { count: entry.count } }))}
                  series={[{ key: "count", label: "Bookings", colorVar: "navy" }]}
                />
              )}
            </Card>
          </section>

          <Card className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Latest</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Recent bookings</h2>
            </div>
            {recent.length === 0 ? (
              <p className="text-sm text-ink-soft">No confirmed bookings in this window yet.</p>
            ) : (
              <ul className="divide-y divide-line/70">
                {recent.map((call) => (
                  <li key={call.callId}>
                    <Link
                      href={`/calls/${call.callId}`}
                      className="flex items-center justify-between gap-4 py-3 transition-colors hover:opacity-80"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-ink">{call.fromNumber || "Unknown caller"}</p>
                        <p className="truncate text-xs text-ink-soft">{call.summary || "Confirmed booking"}</p>
                      </div>
                      <div className="flex shrink-0 items-center gap-3">
                        {call.bookingAction ? (
                          <StatusChip tone="good" label={labelAction(call.bookingAction.split(",")[0])} />
                        ) : null}
                        <span className="whitespace-nowrap text-xs text-ink-soft">
                          {call.day} {call.startTime}
                        </span>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
