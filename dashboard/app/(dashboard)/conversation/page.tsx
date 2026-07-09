import { Bars } from "@/components/charts/Bars";
import { Donut } from "@/components/charts/Donut";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { KpiCard } from "@/components/ui/KpiCard";
import { TabHeader } from "@/components/ui/TabHeader";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { dayBuckets, kpiDelta, previousWindow } from "@/lib/kpi";
import {
  filterByRange,
  intentBreakdown,
  negativeRate,
  parseRange,
  positiveRate,
  sentimentBreakdown,
  spamOverTime,
  spamRate,
  stalledCount,
  stalledPerDay
} from "@/lib/metrics";
import { formatDayShort, formatNumber, formatPercent, formatRangeEyebrow } from "@/lib/utils/format";

export const dynamic = "force-dynamic";

function Icon({ name }: { name: "positive" | "shield" | "stalled" | "negative" }) {
  const paths: Record<string, string> = {
    positive: "M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    shield: "M12 3 5 6v5c0 4 3 7 7 8 4-1 7-4 7-8V6l-7-3Z",
    stalled: "M12 8v4M12 16h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    negative: "M16 15s-1.5-2-4-2-4 2-4 2M9 9h.01M15 9h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
  };

  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d={paths[name]} />
    </svg>
  );
}

function formatIntentLabel(intent: string): string {
  return intent
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default async function ConversationPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);
  const calls = filterByRange(await getCachedCalls(), range);
  const previous = previousWindow(calls);
  const buckets = dayBuckets(calls);
  const sentiments = sentimentBreakdown(calls);
  const spamSeries = spamOverTime(calls);
  const droppedSeries = stalledPerDay(calls);
  const intents = intentBreakdown(calls);
  const rangeLabel =
    spamSeries.length > 0 ? formatRangeEyebrow(spamSeries[0].date, spamSeries[spamSeries.length - 1].date) : "";

  const positiveDelta = kpiDelta(calls, previous, positiveRate, true);
  const spamDelta = kpiDelta(calls, previous, spamRate, null);
  const droppedDelta = kpiDelta(calls, previous, (entries) => entries.filter((call) => call.isStalled).length, false);
  const negativeDelta = kpiDelta(calls, previous, negativeRate, false);

  const kpis = [
    {
      label: "Positive",
      value: formatPercent(positiveRate(calls)),
      footnote: "Share of calls that ended positive",
      deltaLabel: positiveDelta.label,
      deltaTone: positiveDelta.tone,
      trend: buckets.map((bucket) => positiveRate(bucket)),
      sparkTone: "good" as const,
      icon: <Icon name="positive" />
    },
    {
      label: "Spam filtered",
      value: formatPercent(spamRate(calls)),
      footnote: "Detected and dropped by Harmony before your team",
      deltaLabel: spamDelta.label,
      deltaTone: spamDelta.tone,
      trend: buckets.map((bucket) => spamRate(bucket)),
      sparkTone: "accent" as const,
      icon: <Icon name="shield" />
    },
    {
      label: "Dropped / silent",
      value: formatNumber(stalledCount(calls)),
      footnote: "Calls that went silent or dropped before resolution",
      deltaLabel: droppedDelta.label,
      deltaTone: droppedDelta.tone,
      trend: buckets.map((bucket) => bucket.filter((call) => call.isStalled).length),
      sparkTone: "ink" as const,
      icon: <Icon name="stalled" />
    },
    {
      label: "Negative",
      value: formatPercent(negativeRate(calls)),
      footnote: "Share of calls that ended negative",
      deltaLabel: negativeDelta.label,
      deltaTone: negativeDelta.tone,
      trend: buckets.map((bucket) => negativeRate(bucket)),
      sparkTone: "bad" as const,
      icon: <Icon name="negative" />
    }
  ];

  return (
    <div className="space-y-6">
      <TabHeader
        eyebrow={rangeLabel}
        title="Conversation"
        description="Conversation quality: sentiment, spam Harmony filters out, and calls that dropped or went silent."
        range={range}
      />

      {calls.length === 0 ? (
        <EmptyState
          title="No calls in this window"
          description="Widen the date range or wait for the next sync to see conversation quality."
        />
      ) : (
        <>
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {kpis.map((kpi) => (
              <KpiCard key={kpi.label} {...kpi} />
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_1.2fr]">
            <Card className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Quality</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Sentiment</h2>
              </div>
              <Donut
                segments={[
                  { label: "Positive", value: sentiments.Positive ?? 0, color: "pos" },
                  { label: "Neutral", value: sentiments.Neutral ?? 0, color: "neu" },
                  { label: "Negative", value: sentiments.Negative ?? 0, color: "neg" },
                  { label: "No data", value: sentiments.Unknown ?? 0, color: "unk" }
                ]}
                totalLabel="Calls"
              />
            </Card>

            <Card className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Volume</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Spam vs valid</h2>
              </div>
              <Bars
                data={spamSeries.map((point) => ({
                  label: formatDayShort(point.date),
                  values: { valid: point.valid, spam: point.spam }
                }))}
                series={[
                  { key: "valid", label: "Valid", colorVar: "good" },
                  { key: "spam", label: "Spam", colorVar: "bad-soft" }
                ]}
              />
            </Card>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Card className="space-y-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Intent</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Top intents</h2>
                </div>
                <span className="rounded-full bg-accent/20 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink">
                  New metric
                </span>
              </div>
              {intents.length === 0 ? (
                <EmptyState
                  title="Intent data is just starting"
                  description="Intent is captured from the latest Harmony version onward, so it fills in over time."
                />
              ) : (
                <Bars
                  data={intents.map((entry) => ({
                    label: formatIntentLabel(entry.intent),
                    values: { count: entry.count }
                  }))}
                  series={[{ key: "count", label: "Calls", colorVar: "navy" }]}
                />
              )}
            </Card>

            <Card className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Flow</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Dropped / silent per day</h2>
              </div>
              <Bars
                data={droppedSeries.map((point) => ({
                  label: formatDayShort(point.date),
                  values: { dropped: point.stalled }
                }))}
                series={[{ key: "dropped", label: "Dropped / silent", colorVar: "neu" }]}
              />
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
