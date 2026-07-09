import Link from "next/link";
import { StatCard } from "@/components/StatCard";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { bookingEffectivenessBreakdown } from "@/lib/metrics";

export const dynamic = "force-dynamic";

export default async function ReservasPage() {
  const calls = await getCachedCalls();
  const breakdown = bookingEffectivenessBreakdown(calls);
  const mismatches = calls.filter((call) => call.bookingEffectiveness === "mismatch");

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Reservas</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="Confirmadas" value={`${breakdown.confirmedRate}%`} />
        <StatCard label="Total con accion" value={String(breakdown.total)} />
        <StatCard label="Con discrepancia" value={String(breakdown.mismatch)} />
        <StatCard label="Pendientes" value={String(breakdown.pending)} />
      </div>
      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase text-gray-500">
          Llamadas con discrepancia
        </h2>
        <ul className="divide-y divide-gray-200 rounded-2xl border border-gray-200 bg-white dark:divide-white/10 dark:border-white/10 dark:bg-gray-900">
          {mismatches.map((call) => (
            <li key={call.callId}>
              <Link
                href={`/llamadas/${call.callId}`}
                className="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-white/5"
              >
                {call.day} {call.startTime} - {call.summary}
              </Link>
            </li>
          ))}
          {mismatches.length === 0 ? (
            <li className="px-4 py-6 text-center text-sm text-gray-400">
              Sin discrepancias por ahora.
            </li>
          ) : null}
        </ul>
      </div>
    </div>
  );
}
