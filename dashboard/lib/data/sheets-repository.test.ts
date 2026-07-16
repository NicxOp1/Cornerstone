import { describe, expect, it } from "vitest";
import { applyFilters, SheetsCallsRepository, type SheetsValuesClient } from "./sheets-repository";

const HEADERS = [
  "call_id",
  "day",
  "start_time",
  "duration_s",
  "direction",
  "from_number",
  "to_number",
  "call_successful",
  "sentiment",
  "intent",
  "service_type",
  "action_completed",
  "disconnection_reason",
  "cost_cents",
  "cost_per_min_cents",
  "is_spam",
  "is_stalled",
  "failed_tools",
  "summary",
  "booking_effectiveness",
  "recording_blob_url",
  "transcript_blob_url",
  "synced_at"
];

function makeRow(id: string, overrides: Record<string, string> = {}): string[] {
  const base: Record<string, string> = {
    call_id: id,
    day: "2026-07-08",
    start_time: "10:00",
    duration_s: "60",
    direction: "inbound",
    from_number: "",
    to_number: "",
    call_successful: "True",
    sentiment: "Positive",
    intent: "new_booking",
    service_type: "plumbing",
    action_completed: "True",
    disconnection_reason: "user_hangup",
    cost_cents: "30",
    cost_per_min_cents: "30",
    is_spam: "False",
    is_stalled: "False",
    failed_tools: "",
    tools_used: "",
    summary: "",
    booking_effectiveness: "confirmed",
    recording_blob_url: "",
    transcript_blob_url: "",
    synced_at: "2026-07-08T10:00:00",
    ...overrides
  };

  return HEADERS.map((header) => base[header]);
}

class FakeSheetsValuesClient implements SheetsValuesClient {
  constructor(private rows: string[][]) {}

  async getValues(): Promise<string[][]> {
    return [HEADERS, ...this.rows];
  }
}

describe("applyFilters", () => {
  it("filtra por rango de fechas", () => {
    const calls = [{ day: "2026-07-01" }, { day: "2026-07-08" }, { day: "2026-07-15" }] as any[];

    const result = applyFilters(calls, { dateFrom: "2026-07-05", dateTo: "2026-07-10" });

    expect(result).toHaveLength(1);
    expect(result[0].day).toBe("2026-07-08");
  });

  it("filtra por sentimiento e intent combinados", () => {
    const calls = [
      { sentiment: "Positive", intent: "new_booking" },
      { sentiment: "Negative", intent: "new_booking" }
    ] as any[];

    const result = applyFilters(calls, { sentiment: "Positive", intent: "new_booking" });

    expect(result).toHaveLength(1);
  });
});

describe("SheetsCallsRepository.getCalls", () => {
  it("devuelve las llamadas mapeadas desde la sheet falsa", async () => {
    const client = new FakeSheetsValuesClient([
      makeRow("call_1", { tools_used: "find_customer:ok,create_job:fail" }),
      makeRow("call_2")
    ]);
    const repo = new SheetsCallsRepository(client);

    const calls = await repo.getCalls();

    expect(calls).toHaveLength(2);
    expect(calls[0].callId).toBe("call_1");
    expect(calls[0].toolsUsed).toEqual([
      { name: "find_customer", success: true },
      { name: "create_job", success: false }
    ]);
  });

  it("aplica los filtros pasados", async () => {
    const client = new FakeSheetsValuesClient([
      makeRow("call_1", { service_type: "plumbing" }),
      makeRow("call_2", { service_type: "electrical" })
    ]);
    const repo = new SheetsCallsRepository(client);

    const calls = await repo.getCalls({ serviceType: "electrical" });

    expect(calls).toHaveLength(1);
    expect(calls[0].callId).toBe("call_2");
  });

  it("hoja con solo encabezados devuelve lista vacia", async () => {
    const client = new FakeSheetsValuesClient([]);
    const repo = new SheetsCallsRepository(client);

    const calls = await repo.getCalls();

    expect(calls).toEqual([]);
  });
});

describe("SheetsCallsRepository.getCallById", () => {
  it("encuentra una llamada por id", async () => {
    const client = new FakeSheetsValuesClient([makeRow("call_1"), makeRow("call_2")]);
    const repo = new SheetsCallsRepository(client);

    const call = await repo.getCallById("call_2");

    expect(call?.callId).toBe("call_2");
  });

  it("devuelve null si no existe", async () => {
    const client = new FakeSheetsValuesClient([makeRow("call_1")]);
    const repo = new SheetsCallsRepository(client);

    const call = await repo.getCallById("no_existe");

    expect(call).toBeNull();
  });
});

describe("SheetsCallsRepository.getSummaryMetrics", () => {
  it("devuelve las metricas calculadas sobre todas las llamadas", async () => {
    const client = new FakeSheetsValuesClient([
      makeRow("call_1", { call_successful: "True" }),
      makeRow("call_2", { call_successful: "False" })
    ]);
    const repo = new SheetsCallsRepository(client);

    const summary = await repo.getSummaryMetrics();

    expect(summary.totalCalls).toBe(2);
    expect(summary.successRate).toBe(50);
  });
});
