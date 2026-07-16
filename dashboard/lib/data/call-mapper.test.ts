import { describe, expect, it } from "vitest";
import { mapRowToCall } from "./call-mapper";

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
  "tools_used",
  "summary",
  "booking_effectiveness",
  "recording_blob_url",
  "transcript_blob_url",
  "synced_at"
];

function row(overrides: Record<string, string>): string[] {
  const base: Record<string, string> = {
    call_id: "call_1",
    day: "2026-07-08",
    start_time: "10:00",
    duration_s: "68",
    direction: "inbound",
    from_number: "+15185551234",
    to_number: "+18005551000",
    call_successful: "True",
    sentiment: "Positive",
    intent: "new_booking",
    service_type: "plumbing",
    action_completed: "True",
    disconnection_reason: "user_hangup",
    cost_cents: "42",
    cost_per_min_cents: "37.06",
    is_spam: "False",
    is_stalled: "False",
    failed_tools: "",
    tools_used: "",
    summary: "Booked appointment",
    booking_effectiveness: "confirmed",
    recording_blob_url: "https://blob.example.com/recordings/call_1.wav",
    transcript_blob_url: "https://blob.example.com/transcripts/call_1.json",
    synced_at: "2026-07-08T14:05:00"
  };

  const merged = { ...base, ...overrides };
  return HEADERS.map((header) => merged[header]);
}

describe("mapRowToCall", () => {
  it("mapea todos los campos basicos", () => {
    const call = mapRowToCall(HEADERS, row({}));
    expect(call.callId).toBe("call_1");
    expect(call.durationS).toBe(68);
    expect(call.fromNumber).toBe("+15185551234");
  });

  it("parsea booleanos desde el texto 'True'/'False' que escribe Python", () => {
    const call = mapRowToCall(HEADERS, row({ call_successful: "True", is_spam: "False" }));
    expect(call.callSuccessful).toBe(true);
    expect(call.isSpam).toBe(false);
  });

  it("devuelve null para booleanos vacios o no reconocidos", () => {
    const call = mapRowToCall(HEADERS, row({ call_successful: "" }));
    expect(call.callSuccessful).toBeNull();
  });

  it("separa failed_tools por coma", () => {
    const call = mapRowToCall(HEADERS, row({ failed_tools: "create_job,cancel_appointment" }));
    expect(call.failedTools).toEqual(["create_job", "cancel_appointment"]);
  });

  it("failed_tools vacio da lista vacia, no ['']", () => {
    const call = mapRowToCall(HEADERS, row({ failed_tools: "" }));
    expect(call.failedTools).toEqual([]);
  });

  it("parsea tools_used en pares nombre:estado", () => {
    const call = mapRowToCall(HEADERS, row({ tools_used: "find_customer:ok,create_job:fail" }));
    expect(call.toolsUsed).toEqual([
      { name: "find_customer", success: true },
      { name: "create_job", success: false }
    ]);
  });

  it("tolera espacios, saltos de linea y filas antiguas sin estado", () => {
    const call = mapRowToCall(
      HEADERS.map((header) => (header === "tools_used" ? "Tools Used" : header)),
      row({ tools_used: " find_customer\ncreate_job " })
    );

    expect(call.toolsUsed).toEqual([
      { name: "find_customer", success: true },
      { name: "create_job", success: true }
    ]);
  });

  it("tools_used vacio da lista vacia", () => {
    const call = mapRowToCall(HEADERS, row({ tools_used: "" }));
    expect(call.toolsUsed).toEqual([]);
  });

  it("booking_effectiveness vacio default a pending", () => {
    const call = mapRowToCall(HEADERS, row({ booking_effectiveness: "" }));
    expect(call.bookingEffectiveness).toBe("pending");
  });

  it("numeros no parseables caen a 0 en vez de NaN", () => {
    const call = mapRowToCall(HEADERS, row({ duration_s: "" }));
    expect(call.durationS).toBe(0);
  });

  it("headers reordenados igual mapean bien (lectura por nombre, no por indice)", () => {
    const reordered = [...HEADERS].reverse();
    const reorderedRow = row({}).slice().reverse();
    const call = mapRowToCall(reordered, reorderedRow);
    expect(call.callId).toBe("call_1");
    expect(call.durationS).toBe(68);
  });
});
