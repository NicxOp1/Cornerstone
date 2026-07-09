import { CategoryChart } from "@/components/CategoryChart";
import { StatCard } from "@/components/StatCard";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { sentimentBreakdown } from "@/lib/metrics";

export const dynamic = "force-dynamic";

export default async function ConversacionPage() {
  const calls = await getCachedCalls();
  const sentiments = sentimentBreakdown(calls);
  const spamCount = calls.filter((call) => call.isSpam).length;
  const stalledCount = calls.filter((call) => call.isStalled).length;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Conversacion</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Llamadas spam" value={String(spamCount)} />
        <StatCard label="Llamadas estancadas" value={String(stalledCount)} />
        <StatCard label="Total analizadas" value={String(calls.length)} />
      </div>
      <CategoryChart
        data={Object.entries(sentiments).map(([name, value]) => ({
          name,
          value
        }))}
      />
    </div>
  );
}
