"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
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
      setError("No se pudo enviar el comentario. El texto sigue aca, proba de nuevo.");
      return;
    }

    setComment("");
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold uppercase text-gray-500">Comentarios</h2>

      {initialFeedback.length > 0 ? (
        <ul className="space-y-3">
          {initialFeedback.map((entry) => (
            <li key={entry.id} className="rounded-xl border border-gray-200 p-3 dark:border-white/10">
              <p className="text-sm">{entry.comment}</p>
              <p className="mt-1 text-xs text-gray-400">
                {entry.status === "resuelto" ? "Resuelto" : "Pendiente"}
              </p>
              {entry.reply ? (
                <div className="mt-2 rounded-lg bg-gray-50 p-2 text-sm dark:bg-white/5">
                  <p className="text-xs font-medium text-gray-500">Respuesta del equipo</p>
                  <p>{entry.reply}</p>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Dejar un comentario sobre esta llamada"
          className="min-h-24 w-full rounded-lg border border-gray-300 p-3 text-base"
          required
        />
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={sending}
          className="h-11 rounded-lg bg-cornerstone-navy px-4 font-semibold text-cornerstone-yellow disabled:opacity-60"
        >
          {sending ? "Enviando..." : "Enviar comentario"}
        </button>
      </form>
    </div>
  );
}
