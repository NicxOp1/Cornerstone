import { unstable_cache } from "next/cache";
import type { CallFilters } from "@/lib/data/repository";
import { buildProductionRepository } from "@/lib/data/sheets-repository";

const repository = buildProductionRepository();

export function getCachedCalls(filters: CallFilters = {}) {
  return unstable_cache(() => repository.getCalls(filters), ["calls", JSON.stringify(filters)], {
    revalidate: 60,
    tags: ["calls"]
  })();
}

export function getCachedCallById(callId: string) {
  return unstable_cache(() => repository.getCallById(callId), ["calls", "byId", callId], {
    revalidate: 60,
    tags: ["calls"]
  })();
}

export function getCachedSummaryMetrics() {
  return unstable_cache(() => repository.getSummaryMetrics(), ["calls", "summary"], {
    revalidate: 60,
    tags: ["summary"]
  })();
}
