import Link from "next/link";
import type { Call } from "@/lib/types/call";

interface CallsTableProps {
  calls: Call[];
}

export function CallsTable({ calls }: CallsTableProps) {
  if (calls.length === 0) {
    return (
      <p className="rounded-[24px] border border-line bg-card p-6 text-center text-sm text-ink-soft">
        No calls match these filters.
      </p>
    );
  }

  return (
    <>
      <ul className="space-y-2 md:hidden">
        {calls.map((call) => (
          <li key={call.callId}>
            <Link href={`/calls/${call.callId}`} className="block rounded-[24px] border border-line bg-card p-4 shadow-sm">
              <div className="flex justify-between text-sm font-medium">
                <span>{call.fromNumber || "Unknown number"}</span>
                <span>{call.callSuccessful ? "OK" : "NO"}</span>
              </div>
              <p className="text-xs text-ink-soft">
                {call.day} {call.startTime} / {call.durationS}s
              </p>
              <p className="text-xs text-ink-soft">
                {call.serviceType || "No service"} / {call.sentiment || "Unknown"}
              </p>
            </Link>
          </li>
        ))}
      </ul>

      <table className="hidden w-full overflow-hidden rounded-[28px] border border-line bg-card text-sm md:table">
        <thead className="bg-muted text-left text-xs uppercase text-ink-soft">
          <tr>
            <th className="px-4 py-2">Date</th>
            <th className="px-4 py-2">Phone</th>
            <th className="px-4 py-2">Duration</th>
            <th className="px-4 py-2">Service</th>
            <th className="px-4 py-2">Sentiment</th>
            <th className="px-4 py-2">Success</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {calls.map((call) => (
            <tr key={call.callId} className="hover:bg-muted/70">
              <td className="px-4 py-2">
                <Link href={`/calls/${call.callId}`} className="block">
                  {call.day} {call.startTime}
                </Link>
              </td>
              <td className="px-4 py-2">{call.fromNumber || "-"}</td>
              <td className="px-4 py-2">{call.durationS}s</td>
              <td className="px-4 py-2">{call.serviceType || "-"}</td>
              <td className="px-4 py-2">{call.sentiment || "-"}</td>
              <td className="px-4 py-2">{call.callSuccessful ? "OK" : "NO"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
