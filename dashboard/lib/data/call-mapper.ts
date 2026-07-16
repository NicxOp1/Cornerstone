import type { BookingEffectiveness, Call, ToolUsage } from "@/lib/types/call";

function parseBoolCell(value: string): boolean | null {
  if (value === "True" || value === "true") return true;
  if (value === "False" || value === "false") return false;
  return null;
}

function parseNumberCell(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && value !== "" ? parsed : 0;
}

function parseToolsUsed(value: string): ToolUsage[] {
  const raw = value.trim();
  if (!raw) return [];

  const entries = raw
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean);

  return entries.flatMap((entry) => {
    const separator = entry.lastIndexOf(":");
    const name = (separator >= 0 ? entry.slice(0, separator) : entry).trim();
    const status = (separator >= 0 ? entry.slice(separator + 1) : "").trim().toLowerCase();

    if (!name) return [];

    // Older rows sometimes contained only the tool name. They still represent
    // a tool that was used, so keep them visible instead of painting them as a
    // failure just because no status was persisted.
    const success = separator < 0 || ["ok", "success", "succeeded", "true", "done"].includes(status);
    return [{ name, success }];
  });
}

export function mapRowToCall(headers: string[], row: string[]): Call {
  const normalizedHeaders = headers.map((header) =>
    header.trim().toLowerCase().replace(/[\s-]+/g, "_")
  );

  const get = (name: string): string => {
    const index = normalizedHeaders.indexOf(name);
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
    toolsUsed: parseToolsUsed(get("tools_used")),
    summary: get("summary"),
    bookingEffectiveness: (get("booking_effectiveness") || "pending") as BookingEffectiveness,
    bookingAction: get("booking_action"),
    recordingBlobUrl: get("recording_blob_url"),
    transcriptBlobUrl: get("transcript_blob_url"),
    syncedAt: get("synced_at")
  };
}
