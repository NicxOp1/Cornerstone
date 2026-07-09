import { StatCard } from "@/components/StatCard";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { averageCostPerMinuteCents } from "@/lib/metrics";

export const dynamic = "force-dynamic";

export default async function CostoPage() {
  const calls = await getCachedCalls();
  const avgPerMin = averageCostPerMinuteCents(calls);
  const totalCents = calls.reduce((accumulator, call) => accumulator + call.costCents, 0);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Costo</h1>
      <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-white/10 dark:bg-gray-900">
        <p className="text-xs uppercase tracking-wide text-gray-500">Costo promedio por minuto</p>
        <p className="mt-1 text-4xl font-bold text-cornerstone-navy dark:text-white">
          ${(avgPerMin / 100).toFixed(2)}
        </p>
      </div>
      <p className="text-xs text-gray-400">Costo total del periodo: ${(totalCents / 100).toFixed(2)}</p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <StatCard label="Llamadas analizadas" value={String(calls.length)} />
        <StatCard label="Costo total" value={`$${(totalCents / 100).toFixed(2)}`} />
      </div>
    </div>
  );
}
