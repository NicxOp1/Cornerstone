import type { BookingEffectiveness, Call } from "@/lib/types/call";

function parseBoolCell(value: string): boolean | null {
  if (value === "True" || value === "true") return true;
  if (value === "False" || value === "false") return false;
  return null;
}

function parseNumberCell(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && value !== "" ? parsed : 0;
}

export function mapRowToCall(headers: string[], row: string[]): Call {
  const get = (name: string): string => {
    const index = headers.indexOf(name);
    return index >= 0 && index < row.length ? row[index] : "";
  };

  return {
    callId: get("call_id"),
    day: get("day"),
    startTime: get("start_time"),
    durationS: parseNumberCell(get("duration_s")),
    direction: get("direction"),
    fromNumber: get("from_number"),
    toNumber: get("to_number"),
    callSuccessful: parseBoolCell(get("call_successful")),
    sentiment: get("sentiment"),
    intent: get("intent"),
    serviceType: get("service_type"),
    actionCompleted: parseBoolCell(get("action_completed")),
    disconnectionReason: get("disconnection_reason"),
    costCents: parseNumberCell(get("cost_cents")),
    costPerMinCents: parseNumberCell(get("cost_per_min_cents")),
    isSpam: parseBoolCell(get("is_spam")) ?? false,
    isStalled: parseBoolCell(get("is_stalled")) ?? false,
    failedTools: get("failed_tools") ? get("failed_tools").split(",") : [],
    summary: get("summary"),
    bookingEffectiveness: (get("booking_effectiveness") || "pending") as BookingEffectiveness,
    bookingAction: get("booking_action"),
    recordingBlobUrl: get("recording_blob_url"),
    transcriptBlobUrl: get("transcript_blob_url"),
    syncedAt: get("synced_at")
  };
}
