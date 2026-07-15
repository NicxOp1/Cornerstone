"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SegmentToggle } from "@/components/ui/SegmentToggle";
import { StatusChip } from "@/components/ui/StatusChip";
import type { CallbackEntry, CallbackKind } from "@/lib/types/callback";
import { isCallbackPending } from "@/lib/types/callback";
import { cn } from "@/lib/utils/cn";

interface CallbacksExplorerProps {
  emergencyCallbacks: CallbackEntry[];
  generalCallbacks: CallbackEntry[];
}

function sortEntries(entries: CallbackEntry[]): CallbackEntry[] {
  return [...entries].sort((left, right) => {
    const leftPending = isCallbackPending(left.status);
    const rightPending = isCallbackPending(right.status);

    if (leftPending !== rightPending) {
      return leftPending ? -1 : 1;
    }

    return right.timestamp.localeCompare(left.timestamp);
  });
}

export function CallbacksExplorer({ emergencyCallbacks, generalCallbacks }: CallbacksExplorerProps) {
  const [kind, setKind] = useState<CallbackKind>("emergency");
  const [emergency, setEmergency] = useState(emergencyCallbacks);
  const [general, setGeneral] = useState(generalCallbacks);
  const [pendingCallId, setPendingCallId] = useState<string | null>(null);
  const [errorCallId, setErrorCallId] = useState<string | null>(null);

  const entries = kind === "emergency" ? emergency : general;
  const setEntries = kind === "emergency" ? setEmergency : setGeneral;
  const sorted = sortEntries(entries);

  async function markReviewed(callId: string) {
    setPendingCallId(callId);
    setErrorCallId(null);
    const previous = entries;
    setEntries(entries.map((entry) => (entry.callId === callId ? { ...entry, status: "Reviewed" } : entry)));

    try {
      const response = await fetch(`/api/callbacks/${kind}/${callId}/reviewed`, { method: "PATCH" });
      if (!response.ok) {
        throw new Error("request failed");
      }
    } catch {
      setEntries(previous);
      setErrorCallId(callId);
    } finally {
      setPendingCallId(null);
    }
  }

  return (
    <div className="space-y-4">
      <SegmentToggle
        options={[
          { label: "Emergency", value: "emergency" as CallbackKind },
          { label: "General", value: "general" as CallbackKind }
        ]}
        value={kind}
        onChange={setKind}
      />

      {sorted.length === 0 ? (
        <EmptyState title="No callbacks here" description="Nothing logged in this list yet." />
      ) : (
        <div className="space-y-3">
          {sorted.map((entry) => {
            const pending = isCallbackPending(entry.status);

            return (
              <Card key={entry.callId} className={cn(kind === "emergency" && "border-l-[3px] border-l-bad")}>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-ink">{entry.fullName || "Unknown caller"}</p>
                      <StatusChip tone={pending ? "warn" : "good"} label={entry.status || "Pending"} />
                    </div>
                    <p className="text-sm text-ink-soft">{entry.reasonForCall || "—"}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-soft">
                      {entry.phoneNumber ? (
                        <a href={`tel:${entry.phoneNumber}`} className="text-accent">
                          {entry.phoneNumber}
                        </a>
                      ) : (
                        <span>No callback number on file</span>
                      )}
                      {entry.email ? <span>{entry.email}</span> : null}
                      {entry.preferredCallbackTime ? <span>Prefers: {entry.preferredCallbackTime}</span> : null}
                      <span>{entry.timestamp}</span>
                    </div>
                    {entry.callId ? (
                      <Link href={`/calls/${entry.callId}`} className="text-xs font-semibold text-accent">
                        View call
                      </Link>
                    ) : null}
                    {errorCallId === entry.callId ? (
                      <p className="text-xs font-semibold text-bad">Couldn&apos;t save — try again.</p>
                    ) : null}
                  </div>

                  {pending ? (
                    <button
                      type="button"
                      onClick={() => markReviewed(entry.callId)}
                      disabled={pendingCallId === entry.callId}
                      className="shrink-0 rounded-full border border-line px-4 py-1.5 text-sm font-semibold text-ink transition-colors hover:bg-muted disabled:opacity-50"
                    >
                      Mark as reviewed
                    </button>
                  ) : null}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
