export type BookingEffectiveness =
  | "confirmed"
  | "mismatch"
  | "not_applicable"
  | "pending";

export interface ToolUsage {
  name: string;
  success: boolean;
}

export interface Call {
  callId: string;
  day: string;
  startTime: string;
  durationS: number;
  direction: string;
  fromNumber: string;
  toNumber: string;
  callSuccessful: boolean | null;
  sentiment: string;
  intent: string;
  serviceType: string;
  actionCompleted: boolean | null;
  disconnectionReason: string;
  costCents: number;
  costPerMinCents: number;
  isSpam: boolean;
  isStalled: boolean;
  failedTools: string[];
  toolsUsed: ToolUsage[];
  summary: string;
  bookingEffectiveness: BookingEffectiveness;
  bookingAction: string;
  recordingBlobUrl: string;
  transcriptBlobUrl: string;
  syncedAt: string;
}
