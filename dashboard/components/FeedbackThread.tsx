"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { StatusChip } from "@/components/ui/StatusChip";
import type { FeedbackEntry } from "@/lib/types/feedback";

interface FeedbackThreadProps {
  callId: string;
  initialFeedback: FeedbackEntry[];
}

export function FeedbackThread({ callId, initialFeedback }: FeedbackThreadProps) {
  const router = useRouter();
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSending(true);
    setError(null);

    const response = await fetch("/api/feedback", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ callId, comment })
    });

    setSending(false);

    if (!response.ok) {
      setError("Could not send your comment. Your text is still here — try again.");
      return;
    }

    setComment("");
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">Feedback</h2>

      {initialFeedback.length > 0 ? (
        <ul className="space-y-3">
          {initialFeedback.map((entry) => (
            <li key={entry.id} className="rounded-[20px] border border-line/80 bg-card p-4">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-ink">{entry.comment}</p>
                <StatusChip
                  tone={entry.status === "resuelto" ? "good" : "warn"}
                  label={entry.status === "resuelto" ? "Resolved" : "Open"}
                />
              </div>
              {entry.reply ? (
                <div className="mt-3 rounded-[16px] bg-muted/60 p-3 text-sm text-ink">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-soft">Team reply</p>
                  <p className="mt-1">{entry.reply}</p>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Leave a comment on this call"
          className="min-h-24 w-full rounded-[20px] border border-line bg-card p-4 text-base text-ink outline-none focus:border-navy/30"
          required
        />
        {error ? <p className="text-sm text-bad">{error}</p> : null}
        <button
          type="submit"
          disabled={sending}
          className="h-11 rounded-full bg-navy px-5 text-sm font-semibold text-white transition hover:bg-navy-2 disabled:opacity-60"
        >
          {sending ? "Sending…" : "Send comment"}
        </button>
      </form>
    </div>
  );
}
