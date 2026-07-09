"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { MessageSender } from "@/lib/types/message";

interface MessageComposerProps {
  defaultSender: MessageSender;
}

export function MessageComposer({ defaultSender }: MessageComposerProps) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [sender, setSender] = useState<MessageSender>(defaultSender);
  const [sending, setSending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!text.trim()) {
      return;
    }

    setSending(true);

    await fetch("/api/messages", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, sender })
    });

    setText("");
    setSending(false);
    router.refresh();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="sticky bottom-0 flex items-end gap-2 border-t border-gray-200 bg-white p-3 dark:border-white/10 dark:bg-gray-950"
      style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
    >
      <select
        value={sender}
        onChange={(event) => setSender(event.target.value as MessageSender)}
        className="h-11 rounded-lg border border-gray-300 px-2 text-sm"
        aria-label="Escribir como"
      >
        <option value="john">John</option>
        <option value="equipo">Equipo</option>
      </select>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Escribir un mensaje..."
        className="h-11 flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-base"
      />
      <button
        type="submit"
        disabled={sending}
        className="h-11 rounded-lg bg-cornerstone-navy px-4 font-semibold text-cornerstone-yellow disabled:opacity-60"
      >
        Enviar
      </button>
    </form>
  );
}
