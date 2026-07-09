import type { Call } from "@/lib/types/call";
import { parseDay } from "@/lib/utils/format";

export interface SummaryMetrics {
  totalCalls: number;
  successRate: number;
  avgDurationS: number;
  avgCostPerMinCents: number;
  bookingConfirmedRate: number;
  lastSyncedAt: string | null;
}

export interface DailySeriesPoint {
  date: string;
  total: number;
  success: number;
  fail: number;
}

export interface MetricDelta {
  current: number;
  previous: number;
  changePercent: number | null;
}

function roundToOneDecimal(value: number): number {
  return Math.round(value * 10) / 10;
}

function roundToTwoDecimals(value: number): number {
  return Math.round(value * 100) / 100;
}

function parseHour(startTime: string): number | null {
  const match = /^(\d{1,2})/.exec(startTime);

  if (!match) {
    return null;
  }

  const hour = Number(match[1]);
  return Number.isInteger(hour) && hour >= 0 && hour <= 23 ? hour : null;
}

function normalizeSentiment(sentiment: string): "Negative" | "Neutral" | "Positive" | "Unknown" {
  const normalized = sentiment.trim().toLowerCase();

  if (normalized === "positive") {
    return "Positive";
  }

  if (normalized === "neutral") {
    return "Neutral";
  }

  if (normalized === "negative") {
    return "Negative";
  }

  return "Unknown";
}

export function sumCostCents(calls: Call[]): number {
  return calls.reduce((total, call) => total + call.costCents, 0);
}

export function averageCostPerMinuteCents(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  const totalDurationSeconds = calls.reduce((total, call) => total + Math.max(call.durationS, 0), 0);

  if (totalDurationSeconds > 0) {
    return roundToTwoDecimals(sumCostCents(calls) / (totalDurationSeconds / 60));
  }

  const populated = calls.filter((call) => call.costPerMinCents > 0);

  if (populated.length === 0) {
    return 0;
  }

  return roundToTwoDecimals(
    populated.reduce((total, call) => total + call.costPerMinCents, 0) / populated.length
  );
}

export function successRate(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  const successful = calls.filter((call) => call.callSuccessful === true).length;
  return roundToOneDecimal((successful / calls.length) * 100);
}

export function averageDurationSeconds(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  return Math.round(calls.reduce((total, call) => total + call.durationS, 0) / calls.length);
}

export function bookingEffectivenessBreakdown(calls: Call[]) {
  const applicable = calls.filter((call) => call.bookingEffectiveness !== "not_applicable");
  const confirmed = applicable.filter((call) => call.bookingEffectiveness === "confirmed").length;
  const mismatch = applicable.filter((call) => call.bookingEffectiveness === "mismatch").length;
  const pending = applicable.filter((call) => call.bookingEffectiveness === "pending").length;

  return {
    total: applicable.length,
    confirmed,
    mismatch,
    pending,
    confirmedRate: applicable.length ? roundToOneDecimal((confirmed / applicable.length) * 100) : 0
  };
}

export function sentimentBreakdown(calls: Call[]): Record<string, number> {
  const counts: Record<string, number> = {
    Positive: 0,
    Neutral: 0,
    Negative: 0,
    Unknown: 0
  };

  for (const call of calls) {
    const key = normalizeSentiment(call.sentiment);
    counts[key] += 1;
  }

  return Object.fromEntries(Object.entries(counts).filter(([, value]) => value > 0));
}

export function dailySeries(calls: Call[]): DailySeriesPoint[] {
  const buckets = new Map<string, DailySeriesPoint>();

  for (const call of calls) {
    if (!call.day) {
      continue;
    }

    const bucket = buckets.get(call.day) ?? {
      date: call.day,
      total: 0,
      success: 0,
      fail: 0
    };

    bucket.total += 1;

    if (call.callSuccessful === true) {
      bucket.success += 1;
    } else {
      bucket.fail += 1;
    }

    buckets.set(call.day, bucket);
  }

  return [...buckets.values()].sort((left, right) => left.date.localeCompare(right.date));
}

export function hourWeekdayMatrix(calls: Call[]): number[][] {
  const matrix = Array.from({ length: 7 }, () => Array.from({ length: 24 }, () => 0));

  for (const call of calls) {
    const day = parseDay(call.day);
    const hour = parseHour(call.startTime);

    if (!day || hour === null) {
      continue;
    }

    const mondayIndex = (day.getUTCDay() + 6) % 7;
    matrix[mondayIndex][hour] += 1;
  }

  return matrix;
}

export function spamCount(calls: Call[]): number {
  return calls.filter((call) => call.isSpam).length;
}

export function spamRate(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  return roundToOneDecimal((spamCount(calls) / calls.length) * 100);
}

export function stalledCount(calls: Call[]): number {
  return calls.filter((call) => call.isStalled).length;
}

export function positiveRate(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  const positives = calls.filter((call) => normalizeSentiment(call.sentiment) === "Positive").length;
  return roundToOneDecimal((positives / calls.length) * 100);
}

export function negativeRate(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  const negatives = calls.filter((call) => normalizeSentiment(call.sentiment) === "Negative").length;
  return roundToOneDecimal((negatives / calls.length) * 100);
}

export function mostRecentSyncedAt(calls: Call[]): string | null {
  if (calls.length === 0) {
    return null;
  }

  return calls.reduce(
    (latest, call) => (call.syncedAt > latest ? call.syncedAt : latest),
    calls[0].syncedAt
  );
}

export function periodDelta(
  currentCalls: Call[],
  previousCalls: Call[],
  metricFn: (calls: Call[]) => number
): MetricDelta {
  const current = metricFn(currentCalls);
  const previous = metricFn(previousCalls);

  if (previousCalls.length === 0) {
    return { current, previous, changePercent: null };
  }

  if (previous === 0) {
    return { current, previous, changePercent: current === 0 ? 0 : null };
  }

  return {
    current,
    previous,
    changePercent: roundToOneDecimal(((current - previous) / Math.abs(previous)) * 100)
  };
}

export type RangeOption = "7" | "30" | "all";

export function parseRange(value: string | string[] | undefined): RangeOption {
  if (value === "7" || value === "all") {
    return value;
  }

  return "30";
}

export function filterByRange(calls: Call[], range: RangeOption): Call[] {
  if (range === "all") {
    return calls;
  }

  const days = calls.map((call) => call.day).filter(Boolean);

  if (days.length === 0) {
    return calls;
  }

  const anchor = parseDay(days.reduce((latest, day) => (day > latest ? day : latest), days[0]));

  if (!anchor) {
    return calls;
  }

  const windowSize = range === "7" ? 7 : 30;
  const start = new Date(anchor.getTime());
  start.setUTCDate(start.getUTCDate() - (windowSize - 1));

  return calls.filter((call) => {
    const day = parseDay(call.day);
    return day !== null && day >= start && day <= anchor;
  });
}

function bucketByDay<T>(calls: Call[], seed: () => T, add: (acc: T, call: Call) => void): Array<{ date: string } & T> {
  const buckets = new Map<string, T>();

  for (const call of calls) {
    if (!call.day) {
      continue;
    }

    const bucket = buckets.get(call.day) ?? seed();
    add(bucket, call);
    buckets.set(call.day, bucket);
  }

  return [...buckets.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, value]) => ({ date, ...value }));
}

export function costPerDay(calls: Call[]): Array<{ date: string; cents: number }> {
  return bucketByDay(
    calls,
    () => ({ cents: 0 }),
    (acc, call) => {
      acc.cents += call.costCents;
    }
  );
}

export function costPerCallCents(calls: Call[]): number {
  if (calls.length === 0) {
    return 0;
  }

  return roundToTwoDecimals(sumCostCents(calls) / calls.length);
}

export function monthlyProjectionCents(calls: Call[]): number {
  const distinctDays = new Set(calls.map((call) => call.day).filter(Boolean)).size;

  if (distinctDays === 0) {
    return 0;
  }

  return Math.round((sumCostCents(calls) / distinctDays) * 30);
}

export function spamOverTime(calls: Call[]): Array<{ date: string; spam: number; valid: number; total: number }> {
  return bucketByDay(
    calls,
    () => ({ spam: 0, valid: 0, total: 0 }),
    (acc, call) => {
      acc.total += 1;
      if (call.isSpam) {
        acc.spam += 1;
      } else {
        acc.valid += 1;
      }
    }
  );
}

export function stalledPerDay(calls: Call[]): Array<{ date: string; stalled: number }> {
  return bucketByDay(
    calls,
    () => ({ stalled: 0 }),
    (acc, call) => {
      if (call.isStalled) {
        acc.stalled += 1;
      }
    }
  );
}

export function intentBreakdown(calls: Call[]): Array<{ intent: string; count: number }> {
  const counts = new Map<string, number>();

  for (const call of calls) {
    const intent = (call.intent || "").trim().toLowerCase();

    if (!intent || intent === "unknown") {
      continue;
    }

    counts.set(intent, (counts.get(intent) ?? 0) + 1);
  }

  return [...counts.entries()]
    .map(([intent, count]) => ({ intent, count }))
    .sort((left, right) => right.count - left.count);
}

export function computeSummaryMetrics(calls: Call[]): SummaryMetrics {
  const bookingBreakdown = bookingEffectivenessBreakdown(calls);

  return {
    totalCalls: calls.length,
    successRate: successRate(calls),
    avgDurationS: averageDurationSeconds(calls),
    avgCostPerMinCents: averageCostPerMinuteCents(calls),
    bookingConfirmedRate: bookingBreakdown.confirmedRate,
    lastSyncedAt: mostRecentSyncedAt(calls)
  };
}
