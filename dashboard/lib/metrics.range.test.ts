import { describe, expect, it } from "vitest";
import type { Call } from "@/lib/types/call";
import {
  bookingFunnel,
  bookingsByAction,
  confirmedBookings,
  costPerCallCents,
  costPerDay,
  filterByRange,
  intentBreakdown,
  monthlyProjectionCents,
  spamOverTime,
  stalledPerDay
} from "@/lib/metrics";

function makeCall(overrides: Partial<Call> = {}): Call {
  return {
    callId: "c1",
    day: "2026-07-08",
    startTime: "10:00",
    durationS: 120,
    direction: "inbound",
    fromNumber: "1",
    toNumber: "2",
    callSuccessful: true,
    sentiment: "Neutral",
    intent: "unknown",
    serviceType: "",
    actionCompleted: null,
    disconnectionReason: "",
    costCents: 50,
    costPerMinCents: 25,
    isSpam: false,
    isStalled: false,
    failedTools: [],
    toolsUsed: [],
    summary: "",
    bookingEffectiveness: "not_applicable",
    bookingAction: "",
    recordingBlobUrl: "",
    transcriptBlobUrl: "",
    syncedAt: "2026-07-08T10:00:00",
    ...overrides
  };
}

describe("filterByRange", () => {
  const calls = [
    makeCall({ callId: "old", day: "2026-06-01" }),
    makeCall({ callId: "mid", day: "2026-07-05" }),
    makeCall({ callId: "new", day: "2026-07-08" })
  ];

  it("keeps only the last 7 days relative to the latest call", () => {
    const result = filterByRange(calls, "7");
    expect(result.map((call) => call.callId).sort()).toEqual(["mid", "new"]);
  });

  it("returns everything for 'all'", () => {
    expect(filterByRange(calls, "all")).toHaveLength(3);
  });
});

describe("cost metrics", () => {
  const calls = [
    makeCall({ day: "2026-07-07", costCents: 100 }),
    makeCall({ day: "2026-07-07", costCents: 50 }),
    makeCall({ day: "2026-07-08", costCents: 30 })
  ];

  it("sums cost per day sorted by date", () => {
    expect(costPerDay(calls)).toEqual([
      { date: "2026-07-07", cents: 150 },
      { date: "2026-07-08", cents: 30 }
    ]);
  });

  it("computes cost per call", () => {
    expect(costPerCallCents(calls)).toBe(60);
  });

  it("projects a month from the daily pace", () => {
    // total 180 over 2 distinct days => 90/day * 30
    expect(monthlyProjectionCents(calls)).toBe(2700);
  });
});

describe("conversation metrics", () => {
  it("splits spam and valid per day", () => {
    const calls = [
      makeCall({ day: "2026-07-08", isSpam: true }),
      makeCall({ day: "2026-07-08", isSpam: false }),
      makeCall({ day: "2026-07-08", isSpam: false })
    ];
    expect(spamOverTime(calls)).toEqual([{ date: "2026-07-08", spam: 1, valid: 2, total: 3 }]);
  });

  it("counts stalled calls per day", () => {
    const calls = [makeCall({ isStalled: true }), makeCall({ isStalled: false })];
    expect(stalledPerDay(calls)).toEqual([{ date: "2026-07-08", stalled: 1 }]);
  });

  it("breaks down intents excluding unknown, sorted by count", () => {
    const calls = [
      makeCall({ intent: "new_booking" }),
      makeCall({ intent: "new_booking" }),
      makeCall({ intent: "cancel" }),
      makeCall({ intent: "unknown" }),
      makeCall({ intent: "" })
    ];
    expect(intentBreakdown(calls)).toEqual([
      { intent: "new_booking", count: 2 },
      { intent: "cancel", count: 1 }
    ]);
  });
});

describe("booking metrics", () => {
  const calls = [
    makeCall({ isSpam: true }),
    makeCall({ bookingEffectiveness: "confirmed", bookingAction: "schedule" }),
    makeCall({ bookingEffectiveness: "confirmed", bookingAction: "schedule,new_customer" }),
    makeCall({ bookingEffectiveness: "not_applicable" })
  ];

  it("builds the total -> valid -> confirmed funnel", () => {
    expect(bookingFunnel(calls)).toEqual({ total: 4, valid: 3, confirmed: 2 });
  });

  it("counts each booking action, most frequent first", () => {
    expect(bookingsByAction(calls)).toEqual([
      { action: "schedule", count: 2 },
      { action: "new_customer", count: 1 }
    ]);
  });

  it("returns only confirmed bookings", () => {
    expect(confirmedBookings(calls)).toHaveLength(2);
  });
});
