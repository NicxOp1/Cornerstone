"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { MessageSender } from "@/lib/types/message";
import { cn } from "@/lib/utils/cn";

interface MessageComposerProps {
  defaultSender: MessageSender;
}

export function MessageComposer({ defaultSender }: MessageComposerProps) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [sender, setSender] = useState<MessageSender>(defaultSender);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!text.trim()) {
      return;
    }

    setSending(true);
    setError(false);

    const response = await fetch("/api/messages", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, sender })
    });

    setSending(false);

    if (!response.ok) {
      setError(true);
      return;
    }

    setText("");
    router.refresh();
  }

  const asTeam = sender === "equipo";

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-line/70 bg-card p-3"
      style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
    >
      <button
        type="button"
        onClick={() => setSender(asTeam ? "john" : "equipo")}
        aria-pressed={asTeam}
        className={cn(
          "h-11 shrink-0 rounded-full border px-3 text-xs font-semibold transition-colors",
          asTeam ? "border-navy bg-navy text-white" : "border-line bg-muted/50 text-ink-soft"
        )}
      >
        {asTeam ? "As team" : "As John"}
      </button>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Write a message…"
        className="h-11 flex-1 resize-none rounded-[18px] border border-line bg-muted/40 px-4 py-2.5 text-base text-ink outline-none focus:border-navy/30"
      />
      <button
        type="submit"
        disabled={sending}
        className="h-11 rounded-full bg-navy px-5 text-sm font-semibold text-white transition hover:bg-navy-2 disabled:opacity-60"
      >
        {sending ? "Sending…" : "Send"}
      </button>
      {error ? (
        <p className="absolute -top-6 right-3 text-xs text-bad">Could not send — try again.</p>
      ) : null}
    </form>
  );
}
