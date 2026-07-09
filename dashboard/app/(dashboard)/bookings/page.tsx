import { EmptyState } from "@/components/ui/EmptyState";
import { TabHeader } from "@/components/ui/TabHeader";
import { parseRange } from "@/lib/metrics";

export const dynamic = "force-dynamic";

export default function BookingsPage({ searchParams }: { searchParams: { range?: string } }) {
  const range = parseRange(searchParams.range);

  return (
    <div className="space-y-6">
      <TabHeader
        eyebrow=""
        title="Bookings"
        description="Booking outcomes and the confirmation funnel — the next tab to ship."
        range={range}
      />
      <EmptyState
        title="Bookings view is on the way"
        description="This tab gets the funnel, bookings by action, and recent bookings once its plan is implemented."
      />
    </div>
  );
}
