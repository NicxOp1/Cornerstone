import type { Call } from "@/lib/types/call";
import { describe, expect, it } from "vitest";
import {
  averageCostPerMinuteCents,
  averageDurationSeconds,
  bookingEffectivenessBreakdown,
  computeSummaryMetrics,
  dailySeries,
  hourWeekdayMatrix,
  mostRecentSyncedAt,
  periodDelta,
  sentimentBreakdown,
  spamRate,
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
  it("calcula el costo por minuto ponderado por duracion", () => {
    const calls = [
      makeCall({ durationS: 60, costCents: 30, costPerMinCents: 30 }),
      makeCall({ durationS: 180, costCents: 45, costPerMinCents: 15 })
    ];

    expect(averageCostPerMinuteCents(calls)).toBe(18.75);
  });

  it("usa el costo por minuto por llamada como fallback si no hay duracion", () => {
    const calls = [makeCall({ durationS: 0, costPerMinCents: 30 }), makeCall({ durationS: 0, costPerMinCents: 50 })];
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
  it("normaliza sentimientos desconocidos", () => {
    const calls = [
      makeCall({ sentiment: "Positive" }),
      makeCall({ sentiment: " positive " }),
      makeCall({ sentiment: "Negative" }),
      makeCall({ sentiment: "" })
    ];

    expect(sentimentBreakdown(calls)).toEqual({ Positive: 2, Negative: 1, Unknown: 1 });
  });
});

describe("dailySeries", () => {
  it("agrupa por dia con success y fail", () => {
    const calls = [
      makeCall({ day: "2026-07-08", callSuccessful: true }),
      makeCall({ day: "2026-07-08", callSuccessful: false }),
      makeCall({ day: "2026-07-09", callSuccessful: true })
    ];

    expect(dailySeries(calls)).toEqual([
      { date: "2026-07-08", total: 2, success: 1, fail: 1 },
      { date: "2026-07-09", total: 1, success: 1, fail: 0 }
    ]);
  });
});

describe("hourWeekdayMatrix", () => {
  it("ubica las llamadas por dia de semana y hora", () => {
    const calls = [
      makeCall({ day: "2026-07-06", startTime: "10:15" }),
      makeCall({ day: "2026-07-06", startTime: "10:45" }),
      makeCall({ day: "2026-07-07", startTime: "03:00" })
    ];

    const matrix = hourWeekdayMatrix(calls);

    expect(matrix[0][10]).toBe(2);
    expect(matrix[1][3]).toBe(1);
    expect(matrix[6][10]).toBe(0);
  });
});

describe("spamRate", () => {
  it("calcula el porcentaje de spam", () => {
    const calls = [makeCall({ isSpam: true }), makeCall({ isSpam: false }), makeCall({ isSpam: true })];
    expect(spamRate(calls)).toBeCloseTo(66.7, 1);
  });
});

describe("periodDelta", () => {
  it("calcula el delta porcentual contra el periodo previo", () => {
    const current = [makeCall({ durationS: 120 }), makeCall({ durationS: 120 })];
    const previous = [makeCall({ durationS: 60 }), makeCall({ durationS: 60 })];

    expect(periodDelta(current, previous, averageDurationSeconds)).toEqual({
      current: 120,
      previous: 60,
      changePercent: 100
    });
  });

  it("devuelve null si no existe ventana previa", () => {
    expect(periodDelta([makeCall({})], [], averageDurationSeconds).changePercent).toBeNull();
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
