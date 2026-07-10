export interface TranscriptTurn {
  role: "agent" | "user";
  content: string;
}

interface RetellTranscriptEntry {
  role?: unknown;
  content?: unknown;
}

export interface RetellCallPayload {
  recording_multi_channel_url?: string;
  recording_url?: string;
  scrubbed_recording_multi_channel_url?: string;
  scrubbed_recording_url?: string;
  transcript_object?: RetellTranscriptEntry[];
  transcript_with_tool_calls?: RetellTranscriptEntry[];
}

export class RetellCallError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function pickRecordingUrl(call: RetellCallPayload): string {
  return [
    call.recording_url,
    call.scrubbed_recording_url,
    call.recording_multi_channel_url,
    call.scrubbed_recording_multi_channel_url
  ].find((value): value is string => typeof value === "string" && value.trim().length > 0) ?? "";
}

export function extractTranscriptTurns(call: RetellCallPayload): TranscriptTurn[] {
  const source =
    Array.isArray(call.transcript_with_tool_calls) && call.transcript_with_tool_calls.length > 0
      ? call.transcript_with_tool_calls
      : Array.isArray(call.transcript_object)
        ? call.transcript_object
        : [];

  return source
    .filter(
      (entry): entry is TranscriptTurn =>
        Boolean(entry) &&
        (entry.role === "agent" || entry.role === "user") &&
        typeof entry.content === "string" &&
        entry.content.trim().length > 0
    )
    .map((entry) => ({ role: entry.role, content: entry.content }));
}

export async function fetchRetellCall(callId: string): Promise<RetellCallPayload> {
  const apiKey = process.env.RETELL_API_KEY ?? "";
  if (!apiKey.trim()) {
    throw new RetellCallError(500, "RETELL_API_KEY is not configured.");
  }

  const response = await fetch(`https://api.retellai.com/v2/get-call/${callId}`, {
    headers: {
      Authorization: `Bearer ${apiKey}`
    },
    cache: "no-store"
  });

  if (response.status === 404) {
    throw new RetellCallError(404, "Call not found in Retell.");
  }

  if (!response.ok) {
    throw new RetellCallError(502, `Retell returned ${response.status}.`);
  }

  return (await response.json()) as RetellCallPayload;
}
