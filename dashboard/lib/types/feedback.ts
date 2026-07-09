export type FeedbackStatus = "open" | "resuelto";

export interface FeedbackEntry {
  id: string;
  callId: string;
  timestamp: string;
  comment: string;
  status: FeedbackStatus;
  reply: string;
  repliedAt: string;
}
