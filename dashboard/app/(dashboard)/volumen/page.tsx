import { CategoryChart } from "@/components/CategoryChart";
import { StatCard } from "@/components/StatCard";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { averageDurationSeconds, successRate } from "@/lib/metrics";

export const dynamic = "force-dynamic";

export default async function VolumenPage() {
  const calls = await getCachedCalls();
  const byDirection: Record<string, number> = {};

  for (const call of calls) {
    const key = call.direction || "desconocida";
    byDirection[key] = (byDirection[key] ?? 0) + 1;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Volumen</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Llamadas totales" value={String(calls.length)} />
        <StatCard label="Tasa de exito" value={`${successRate(calls)}%`} />
        <StatCard label="Duracion promedio" value={`${averageDurationSeconds(calls)}s`} />
      </div>
      <CategoryChart
        data={Object.entries(byDirection).map(([name, value]) => ({
          name,
          value
        }))}
      />
    </div>
  );
}
