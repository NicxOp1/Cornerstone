import { periodDelta } from "@/lib/metrics";
import type { Call } from "@/lib/types/call";
import { addUtcDays, inclusiveDaySpan, parseDay } from "@/lib/utils/format";

export type DeltaTone = "bad" | "good" | "neutral";

export interface DeltaBadge {
  label: string;
  tone: DeltaTone;
}

export function dayBuckets(calls: Call[]): Call[][] {
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
    .map(([, dayCalls]) => dayCalls);
}

export function previousWindow(calls: Call[]): Call[] {
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
    return callDate !== null && callDate >= previousStart && callDate <= previousEnd;
  });
}

export function deltaBadge(change: number | null, higherIsBetter: boolean | null): DeltaBadge {
  if (change === null) {
    return { label: "First window", tone: "neutral" };
  }

  if (change === 0) {
    return { label: "Flat vs prior", tone: "neutral" };
  }

  const positive = change > 0;
  const tone: DeltaTone =
    higherIsBetter === null ? "neutral" : positive === higherIsBetter ? "good" : "bad";

  return { label: `${positive ? "+" : ""}${change.toFixed(1)}% vs prior`, tone };
}

export function kpiDelta(
  current: Call[],
  previous: Call[],
  metricFn: (calls: Call[]) => number,
  higherIsBetter: boolean | null
): DeltaBadge {
  return deltaBadge(periodDelta(current, previous, metricFn).changePercent, higherIsBetter);
}
