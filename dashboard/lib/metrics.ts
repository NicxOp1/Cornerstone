import type { Call } from "@/lib/types/call";

export interface SummaryMetrics {
  totalCalls: number;
  successRate: number;
  avgDurationS: number;
  avgCostPerMinCents: number;
  bookingConfirmedRate: number;
  lastSyncedAt: string | null;
}

export function averageCostPerMinuteCents(calls: Call[]): number {
  if (calls.length === 0) return 0;
  const sum = calls.reduce((acc, call) => acc + call.costPerMinCents, 0);
  return Math.round((sum / calls.length) * 100) / 100;
}

export function successRate(calls: Call[]): number {
  if (calls.length === 0) return 0;
  const successful = calls.filter((call) => call.callSuccessful === true).length;
  return Math.round((successful / calls.length) * 1000) / 10;
}

export function averageDurationSeconds(calls: Call[]): number {
  if (calls.length === 0) return 0;
  return Math.round(calls.reduce((acc, call) => acc + call.durationS, 0) / calls.length);
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
    confirmedRate: applicable.length
      ? Math.round((confirmed / applicable.length) * 1000) / 10
      : 0
  };
}

export function sentimentBreakdown(calls: Call[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const call of calls) {
    const key = call.sentiment || "Unknown";
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

export function mostRecentSyncedAt(calls: Call[]): string | null {
  if (calls.length === 0) return null;
  return calls.reduce(
    (latest, call) => (call.syncedAt > latest ? call.syncedAt : latest),
    calls[0].syncedAt
  );
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
