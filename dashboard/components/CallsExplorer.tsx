"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { StatusChip, sentimentTone } from "@/components/ui/StatusChip";
import type { Call, ToolUsage } from "@/lib/types/call";
import { formatDuration, formatToolName } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

const PAGE_SIZE = 25;

const SELECTS: Array<{ key: "sentiment" | "result" | "tools"; label: string; options: Array<{ value: string; label: string }> }> = [
  {
    key: "sentiment",
    label: "Sentiment",
    options: [
      { value: "all", label: "All sentiment" },
      { value: "positive", label: "Positive" },
      { value: "neutral", label: "Neutral" },
      { value: "negative", label: "Negative" }
    ]
  },
  {
    key: "result",
    label: "Result",
    options: [
      { value: "all", label: "All results" },
      { value: "success", label: "Resolved" },
      { value: "fail", label: "Unresolved" }
    ]
  },
  {
    key: "tools",
    label: "Tools",
    options: [
      { value: "all", label: "All tools" },
      { value: "ok", label: "All succeeded" },
      { value: "failed", label: "Had a failure" },
      { value: "none", label: "No tools used" }
    ]
  }
];

function ToolsCell({ tools }: { tools: ToolUsage[] }) {
  if (tools.length === 0) {
    return <span className="text-xs text-ink-soft">No tools</span>;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {tools.map((tool, index) => (
        <span
          key={`${tool.name}-${index}`}
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium",
            tool.success ? "bg-good-soft text-good" : "bg-bad-soft text-bad"
          )}
        >
          {formatToolName(tool.name)}
        </span>
      ))}
    </div>
  );
}

export function CallsExplorer({ calls }: { calls: Call[] }) {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({ sentiment: "all", result: "all", tools: "all" });
  const [page, setPage] = useState(0);

  function update(key: "sentiment" | "result" | "tools", value: string) {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  }

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    return calls
      .filter((call) => {
        if (needle && !`${call.fromNumber} ${call.summary}`.toLowerCase().includes(needle)) {
          return false;
        }
        if (filters.sentiment !== "all" && call.sentiment.trim().toLowerCase() !== filters.sentiment) {
          return false;
        }
        if (filters.result === "success" && call.callSuccessful !== true) {
          return false;
        }
        if (filters.result === "fail" && call.callSuccessful === true) {
          return false;
        }
        if (filters.tools === "ok" && (call.toolsUsed.length === 0 || call.toolsUsed.some((tool) => !tool.success))) {
          return false;
        }
        if (filters.tools === "failed" && !call.toolsUsed.some((tool) => !tool.success)) {
          return false;
        }
        if (filters.tools === "none" && call.toolsUsed.length !== 0) {
          return false;
        }
        return true;
      })
      .sort((left, right) => `${right.day}${right.startTime}`.localeCompare(`${left.day}${left.startTime}`));
  }, [calls, query, filters]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pageCount - 1);
  const rows = filtered.slice(current * PAGE_SIZE, (current + 1) * PAGE_SIZE);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-[24px] border border-line/80 bg-card p-4 shadow-panel md:flex-row md:items-center">
        <input
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(0);
          }}
          placeholder="Search phone or summary"
          className="w-full flex-1 rounded-full border border-line bg-muted/70 px-4 py-2.5 text-sm text-ink outline-none focus:border-accent/25 md:max-w-xs"
        />
        <div className="flex flex-wrap gap-2">
          {SELECTS.map((select) => (
            <select
              key={select.key}
              value={filters[select.key]}
              onChange={(event) => update(select.key, event.target.value)}
              aria-label={select.label}
              className="rounded-full border border-line bg-muted/70 px-3.5 py-2.5 text-sm font-medium text-ink-soft outline-none focus:border-accent/25"
            >
              {select.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="rounded-[24px] border border-line bg-card p-8 text-center text-sm text-ink-soft">
          No calls match these filters.
        </p>
      ) : (
        <div className="overflow-hidden rounded-[28px] border border-line/80 bg-card shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead className="border-b border-line/80 bg-muted/60 text-left text-[11px] uppercase tracking-[0.12em] text-ink-soft">
                <tr>
                  <th className="px-5 py-3 font-semibold">Date</th>
                  <th className="px-5 py-3 font-semibold">Caller</th>
                  <th className="px-5 py-3 font-semibold">Duration</th>
                  <th className="px-5 py-3 font-semibold">Sentiment</th>
                  <th className="px-5 py-3 font-semibold">Result</th>
                  <th className="px-5 py-3 font-semibold">Tools</th>
                  <th className="px-5 py-3 font-semibold">Summary</th>
                  <th className="px-5 py-3 text-right font-semibold">Open</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/70">
                {rows.map((call) => (
                  <tr key={call.callId} className="group transition-colors hover:bg-white/[0.03]">
                    <td className="whitespace-nowrap px-5 py-3.5 text-ink-soft">
                      <Link href={`/calls/${call.callId}`} className="block font-medium text-ink">
                        {call.day}
                        <span className="block text-xs text-ink-soft">{call.startTime}</span>
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 tabular-nums text-ink">
                      {call.fromNumber || "Unknown"}
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 tabular-nums text-ink-soft">
                      {formatDuration(call.durationS)}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusChip tone={sentimentTone(call.sentiment)} label={call.sentiment || "Unknown"} />
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusChip
                        tone={call.callSuccessful ? "good" : "neutral"}
                        label={call.callSuccessful ? "Resolved" : "Unresolved"}
                      />
                    </td>
                    <td className="px-5 py-3.5">
                      <ToolsCell tools={call.toolsUsed} />
                    </td>
                    <td className="max-w-[280px] px-5 py-3.5 text-ink-soft">
                      <Link href={`/calls/${call.callId}`} className="line-clamp-1 block">
                        {call.summary || "-"}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 text-right">
                      <Link
                        href={`/calls/${call.callId}`}
                        aria-label="Open call"
                        className="inline-flex items-center gap-1.5 rounded-full border border-line/80 bg-muted/60 px-3.5 py-1.5 text-xs font-semibold text-ink-soft transition-colors hover:border-accent/30 hover:bg-accent/12 hover:text-accent group-hover:border-accent/30 group-hover:text-accent"
                      >
                        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M9 6.5v11l9-5.5-9-5.5Z" />
                        </svg>
                        Open call
                        <svg viewBox="0 0 24 24" className="h-3 w-3" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="m9 6 6 6-6 6" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-4 border-t border-line/80 px-5 py-3 text-sm text-ink-soft">
            <span>
              {filtered.length} call{filtered.length === 1 ? "" : "s"} - page {current + 1} of {pageCount}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPage((value) => Math.max(0, value - 1))}
                disabled={current === 0}
                className={cn(
                  "rounded-full border border-line px-4 py-1.5 text-sm font-semibold transition-colors",
                  current === 0 ? "cursor-not-allowed text-ink-soft/50" : "text-ink hover:bg-muted"
                )}
              >
                Prev
              </button>
              <button
                type="button"
                onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}
                disabled={current >= pageCount - 1}
                className={cn(
                  "rounded-full border border-line px-4 py-1.5 text-sm font-semibold transition-colors",
                  current >= pageCount - 1 ? "cursor-not-allowed text-ink-soft/50" : "text-ink hover:bg-muted"
                )}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
