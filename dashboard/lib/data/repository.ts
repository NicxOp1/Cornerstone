import type { SummaryMetrics } from "@/lib/metrics";
import type { Call } from "@/lib/types/call";

export type { SummaryMetrics };

export interface CallFilters {
  dateFrom?: string;
  dateTo?: string;
  sentiment?: string;
  intent?: string;
  serviceType?: string;
  callSuccessful?: boolean;
}

export interface CallsRepository {
  getCalls(filters?: CallFilters): Promise<Call[]>;
  getCallById(callId: string): Promise<Call | null>;
  getSummaryMetrics(): Promise<SummaryMetrics>;
}
