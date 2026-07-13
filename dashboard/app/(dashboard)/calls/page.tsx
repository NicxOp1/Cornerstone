import { CallsExplorer } from "@/components/CallsExplorer";
import { EmptyState } from "@/components/ui/EmptyState";
import { TabHeader } from "@/components/ui/TabHeader";
import { getCachedCalls } from "@/lib/data/cached-repository";
import { costPerDay, filterByRange, parseRange } from "@/lib/metrics";
import { formatRangeEyebrow } from "@/lib/utils/format";

export const dynamic = "force-dynamic";

export default async function CallsPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);
  const calls = filterByRange(await getCachedCalls(), range);
  const days = costPerDay(calls);
  const rangeLabel = days.length > 0 ? formatRangeEyebrow(days[0].date, days[days.length - 1].date) : "";

  return (
    <div className="space-y-6">
      <TabHeader
        eyebrow={rangeLabel}
        title="Calls"
        description="Every call in this window. Search, filter, and open one to hear it and read the transcript."
        range={range}
      />

      {calls.length === 0 ? (
        <EmptyState
          title="No calls in this window"
          description="Widen the date range or wait for the next sync to see calls here."
        />
      ) : (
        <CallsExplorer calls={calls} />
      )}
    </div>
  );
}
