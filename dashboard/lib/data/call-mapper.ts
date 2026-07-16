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

const SUCCESS_STATUSES = new Set(["ok", "success", "succeeded", "true", "done"]);

const HEADER_ALIASES: Record<string, string[]> = {
  tools_used: ["tools", "tool_used", "tool_calls"]
};

function normalizeHeader(header: string): string {
  return header.trim().toLowerCase().replace(/[\s-]+/g, "_");
}

function parseToolEntry(entry: string): ToolUsage[] {
  const cleaned = entry.trim().replace(/^[\[\]'\"]+|[\]'\"]+$/g, "");
  if (!cleaned) return [];

  const separator = cleaned.lastIndexOf(":");
  const name = (separator >= 0 ? cleaned.slice(0, separator) : cleaned).trim();
  const status = (separator >= 0 ? cleaned.slice(separator + 1) : "")
    .trim()
    .toLowerCase();

  if (!name) return [];

  return [{
    name,
    success: separator < 0 || SUCCESS_STATUSES.has(status)
  }];
}

function parseToolsUsed(value: string): ToolUsage[] {
  const raw = value.trim();
  if (!raw) return [];

  if (raw.startsWith("[") && raw.endsWith("]")) {
    try {
      const parsed: unknown = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed.flatMap((entry) => {
          if (typeof entry === "string") return parseToolEntry(entry);
          if (!entry || typeof entry !== "object") return [];

          const record = entry as { name?: unknown; status?: unknown; success?: unknown };
          if (typeof record.name !== "string") return [];

          const status = typeof record.status === "string"
            ? record.status
            : record.success === true
              ? "ok"
              : record.success === false
                ? "fail"
                : "";

          return parseToolEntry(`${record.name}:${status}`);
        });
      }
    } catch {
      // Legacy Python list repr is handled by the delimiter fallback below.
    }
  }

  const legacyList = raw.startsWith("[") && raw.endsWith("]") ? raw.slice(1, -1) : raw;
  return legacyList.split(/[\n,;|]+/).flatMap(parseToolEntry);
}

export function mapRowToCall(headers: string[], row: string[]): Call {
  const normalizedHeaders = headers.map(normalizeHeader);

  const get = (name: string): string => {
    const candidates = [name, ...(HEADER_ALIASES[name] ?? [])].map(normalizeHeader);
    const index = candidates
      .map((candidate) => normalizedHeaders.indexOf(candidate))
      .find((candidateIndex) => candidateIndex >= 0) ?? -1;
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
