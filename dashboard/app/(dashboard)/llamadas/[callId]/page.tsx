import { notFound } from "next/navigation";
import { AudioPlayer } from "@/components/AudioPlayer";
import { FeedbackThread } from "@/components/FeedbackThread";
import { getCachedCallById, getCachedFeedbackForCall } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

interface CallDetailPageProps {
  params: {
    callId: string;
  };
}

export default async function CallDetailPage({ params }: CallDetailPageProps) {
  const call = await getCachedCallById(params.callId);

  if (!call) {
    notFound();
  }

  const feedback = await getCachedFeedbackForCall(params.callId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">{call.fromNumber || "Numero desconocido"}</h1>
        <p className="text-sm text-gray-500">
          {call.day} {call.startTime} · {call.durationS}s
        </p>
      </div>

      <AudioPlayer recordingBlobUrl={call.recordingBlobUrl} />

      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-gray-100 px-3 py-1 dark:bg-white/10">{call.intent}</span>
        <span className="rounded-full bg-gray-100 px-3 py-1 dark:bg-white/10">{call.sentiment}</span>
        <span className="rounded-full bg-gray-100 px-3 py-1 dark:bg-white/10">
          {call.serviceType || "sin servicio"}
        </span>
        <span className="rounded-full bg-gray-100 px-3 py-1 dark:bg-white/10">
          Reserva: {call.bookingEffectiveness}
        </span>
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase text-gray-500">Resumen</h2>
        <p className="text-sm">{call.summary || "Sin resumen disponible."}</p>
      </div>

      <FeedbackThread callId={call.callId} initialFeedback={feedback} />
    </div>
  );
}
