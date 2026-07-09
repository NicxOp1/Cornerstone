import type { Call } from "@/lib/types/call";
import { describe, expect, it } from "vitest";
import {
  averageCostPerMinuteCents,
  averageDurationSeconds,
  bookingEffectivenessBreakdown,
  computeSummaryMetrics,
  mostRecentSyncedAt,
  sentimentBreakdown,
  successRate
} from "./metrics";

function makeCall(overrides: Partial<Call> = {}): Call {
  return {
    callId: "call_1",
    day: "2026-07-08",
    startTime: "10:00",
    durationS: 60,
    direction: "inbound",
    fromNumber: "",
    toNumber: "",
    callSuccessful: true,
    sentiment: "Positive",
    intent: "new_booking",
    serviceType: "plumbing",
    actionCompleted: true,
    disconnectionReason: "user_hangup",
    costCents: 30,
    costPerMinCents: 30,
    isSpam: false,
    isStalled: false,
    failedTools: [],
    summary: "",
    bookingEffectiveness: "confirmed",
    recordingBlobUrl: "",
    transcriptBlobUrl: "",
    syncedAt: "2026-07-08T14:00:00",
    ...overrides
  };
}

describe("averageCostPerMinuteCents", () => {
  it("promedia el costo por minuto de todas las llamadas", () => {
    const calls = [makeCall({ costPerMinCents: 30 }), makeCall({ costPerMinCents: 50 })];
    expect(averageCostPerMinuteCents(calls)).toBe(40);
  });

  it("devuelve 0 con lista vacia", () => {
    expect(averageCostPerMinuteCents([])).toBe(0);
  });
});

describe("successRate", () => {
  it("calcula el porcentaje de llamadas exitosas", () => {
    const calls = [
      makeCall({ callSuccessful: true }),
      makeCall({ callSuccessful: true }),
      makeCall({ callSuccessful: false })
    ];
    expect(successRate(calls)).toBeCloseTo(66.7, 1);
  });

  it("devuelve 0 con lista vacia", () => {
    expect(successRate([])).toBe(0);
  });
});

describe("averageDurationSeconds", () => {
  it("promedia la duracion", () => {
    const calls = [makeCall({ durationS: 60 }), makeCall({ durationS: 100 })];
    expect(averageDurationSeconds(calls)).toBe(80);
  });
});

describe("bookingEffectivenessBreakdown", () => {
  it("excluye not_applicable del denominador", () => {
    const calls = [
      makeCall({ bookingEffectiveness: "confirmed" }),
      makeCall({ bookingEffectiveness: "mismatch" }),
      makeCall({ bookingEffectiveness: "not_applicable" })
    ];
    const result = bookingEffectivenessBreakdown(calls);
    expect(result.total).toBe(2);
    expect(result.confirmed).toBe(1);
    expect(result.mismatch).toBe(1);
    expect(result.confirmedRate).toBe(50);
  });

  it("total 0 no divide por cero", () => {
    const result = bookingEffectivenessBreakdown([
      makeCall({ bookingEffectiveness: "not_applicable" })
    ]);
    expect(result.confirmedRate).toBe(0);
  });
});

describe("sentimentBreakdown", () => {
  it("cuenta llamadas por sentimiento", () => {
    const calls = [
      makeCall({ sentiment: "Positive" }),
      makeCall({ sentiment: "Positive" }),
      makeCall({ sentiment: "Negative" })
    ];
    expect(sentimentBreakdown(calls)).toEqual({ Positive: 2, Negative: 1 });
  });
});

describe("mostRecentSyncedAt", () => {
  it("devuelve el synced_at mas reciente", () => {
    const calls = [
      makeCall({ syncedAt: "2026-07-08T10:00:00" }),
      makeCall({ syncedAt: "2026-07-08T14:00:00" }),
      makeCall({ syncedAt: "2026-07-08T09:00:00" })
    ];
    expect(mostRecentSyncedAt(calls)).toBe("2026-07-08T14:00:00");
  });

  it("devuelve null con lista vacia", () => {
    expect(mostRecentSyncedAt([])).toBeNull();
  });
});

describe("computeSummaryMetrics", () => {
  it("combina todas las metricas", () => {
    const calls = [
      makeCall({}),
      makeCall({ callSuccessful: false, bookingEffectiveness: "mismatch" })
    ];
    const summary = computeSummaryMetrics(calls);
    expect(summary.totalCalls).toBe(2);
    expect(summary.successRate).toBe(50);
    expect(summary.bookingConfirmedRate).toBe(50);
  });
});
