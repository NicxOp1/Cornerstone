import Link from "next/link";
import { StatCard } from "@/components/StatCard";
import { getCachedCalls, getCachedSummaryMetrics } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

export default async function ResumenPage() {
  const [summary, recentCalls] = await Promise.all([getCachedSummaryMetrics(), getCachedCalls()]);
  const lastFive = [...recentCalls].sort((a, b) => (a.syncedAt < b.syncedAt ? 1 : -1)).slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Resumen</h1>
        <p className="text-sm text-gray-500">
          {summary.lastSyncedAt
            ? `Ultima actualizacion: hace instantes (${summary.lastSyncedAt})`
            : "Todavia no hay llamadas sincronizadas."}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard label="Llamadas totales" value={String(summary.totalCalls)} sublabel="Volumen" />
        <StatCard
          label="Reservas confirmadas"
          value={`${summary.bookingConfirmedRate}%`}
          sublabel="Reservas"
        />
        <StatCard label="Tasa de exito" value={`${summary.successRate}%`} sublabel="Conversacion" />
        <StatCard
          label="Costo promedio / min"
          value={`$${(summary.avgCostPerMinCents / 100).toFixed(2)}`}
          sublabel="Costo"
        />
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase text-gray-500">Ultimas llamadas</h2>
        <ul className="divide-y divide-gray-200 rounded-2xl border border-gray-200 bg-white dark:divide-white/10 dark:border-white/10 dark:bg-gray-900">
          {lastFive.map((call) => (
            <li key={call.callId}>
              <Link
                href={`/llamadas/${call.callId}`}
                className="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-white/5"
              >
                <div className="flex justify-between text-sm">
                  <span>{call.fromNumber || "Numero desconocido"}</span>
                  <span className="text-gray-400">
                    {call.day} {call.startTime}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs text-gray-500">{call.summary}</p>
              </Link>
            </li>
          ))}
          {lastFive.length === 0 ? (
            <li className="px-4 py-6 text-center text-sm text-gray-400">
              Todavia no hay llamadas para mostrar.
            </li>
          ) : null}
        </ul>
      </div>
    </div>
  );
}
