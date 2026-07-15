import Link from "next/link";
import { notFound } from "next/navigation";
import { FeedbackThread } from "@/components/FeedbackThread";
import { WaveformPlayer } from "@/components/WaveformPlayer";
import { Card } from "@/components/ui/Card";
import { StatusChip, bookingLabel, bookingTone, sentimentTone } from "@/components/ui/StatusChip";
import { getCachedCallById, getCachedFeedbackForCall } from "@/lib/data/cached-repository";
import { extractTranscriptTurns, fetchRetellCall, type TranscriptTurn } from "@/lib/retell-call";
import type { Call } from "@/lib/types/call";
import { formatDuration } from "@/lib/utils/format";

export const dynamic = "force-dynamic";

async function loadTranscript(url: string): Promise<TranscriptTurn[]> {
  if (!url) {
    return [];
  }

  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const data = (await response.json()) as unknown;
    if (!Array.isArray(data)) {
      return [];
    }
    return data
      .filter(
        (entry): entry is TranscriptTurn =>
          Boolean(entry) &&
          (entry.role === "agent" || entry.role === "user") &&
          typeof entry.content === "string" &&
          entry.content.trim().length > 0
      )
      .map((entry) => ({ role: entry.role, content: entry.content }));
  } catch {
    return [];
  }
}

async function loadTranscriptFallback(callId: string): Promise<TranscriptTurn[]> {
  try {
    const retellCall = await fetchRetellCall(callId);
    return extractTranscriptTurns(retellCall);
  } catch {
    return [];
  }
}

function heroTint(call: Call): string {
  if (call.bookingEffectiveness === "confirmed") return "good";
  if (call.bookingEffectiveness === "mismatch") return "bad";
  if (call.callSuccessful === true) return "navy-2";
  return "navy-2";
}

function outcomeChip(call: Call) {
  if (call.bookingEffectiveness !== "not_applicable") {
    return <StatusChip tone={bookingTone(call.bookingEffectiveness)} label={bookingLabel(call.bookingEffectiveness)} />;
  }
  return (
    <StatusChip
      tone={call.callSuccessful ? "good" : "neutral"}
      label={call.callSuccessful ? "Resolved" : "Unresolved"}
    />
  );
}

export default async function CallDetailPage({ params }: { params: { callId: string } }) {
  const call = await getCachedCallById(params.callId);

  if (!call) {
    notFound();
  }

  const [feedback, transcript] = await Promise.all([
    getCachedFeedbackForCall(params.callId),
    call.transcriptBlobUrl ? loadTranscript(call.transcriptBlobUrl) : loadTranscriptFallback(params.callId)
  ]);

  const tint = heroTint(call);

  return (
    <div className="space-y-6">
      <Link href="/calls" className="inline-flex items-center gap-2 text-sm font-medium text-ink-soft hover:text-ink">
        <span aria-hidden="true">←</span> Back to calls
      </Link>

      <header
        className="overflow-hidden rounded-[32px] border border-line/40 p-7 text-white shadow-panel md:p-9"
        style={{
          backgroundImage: `linear-gradient(135deg, rgb(var(--${tint})) 0%, rgb(var(--navy)) 62%)`
        }}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/70">
              {call.direction || "call"} · {call.day} {call.startTime}
            </p>
            <h1 className="font-display text-3xl tracking-tight md:text-4xl">
              {call.fromNumber || "Unknown caller"}
            </h1>
            <p className="text-sm text-white/80">{formatDuration(call.durationS)} · {call.intent || "no intent"}</p>
          </div>
          {outcomeChip(call)}
        </div>
      </header>

      <WaveformPlayer
        recordingUrl={call.recordingBlobUrl || `/api/calls/${params.callId}/recording`}
        seed={call.callId}
        durationS={call.durationS}
      />

      <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_1.1fr]">
        <Card className="space-y-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Summary</p>
            <p className="mt-3 text-sm leading-6 text-ink">{call.summary || "No summary available."}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusChip tone={sentimentTone(call.sentiment)} label={call.sentiment || "Unknown"} />
            {call.serviceType ? <StatusChip tone="neutral" label={call.serviceType} /> : null}
            {call.intent ? <StatusChip tone="neutral" label={call.intent} /> : null}
          </div>
        </Card>

        <Card className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Transcript</p>
          {transcript.length === 0 ? (
            <p className="text-sm leading-6 text-ink-soft">
              {call.summary || "Transcript unavailable for this call."}
            </p>
          ) : (
            <ul className="space-y-3">
              {transcript.map((turn, index) => (
                <li key={index} className="flex flex-col gap-1">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-soft">
                    {turn.role === "agent" ? "Harmony" : "Caller"}
                  </span>
                  <p
                    className={
                      turn.role === "agent"
                        ? "rounded-[18px] rounded-tl-sm bg-muted/60 px-4 py-2.5 text-sm text-ink"
                        : "self-end rounded-[18px] rounded-tr-sm bg-navy px-4 py-2.5 text-sm text-white"
                    }
                  >
                    {turn.content}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>

      <Card>
        <FeedbackThread callId={call.callId} initialFeedback={feedback} />
      </Card>
    </div>
  );
}
