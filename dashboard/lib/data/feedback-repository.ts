import { randomUUID } from "crypto";
import type { SheetsWriteClient } from "@/lib/data/sheets-writer";
import type { FeedbackEntry, FeedbackStatus } from "@/lib/types/feedback";

const TAB = "Feedback";
const HEADERS = ["id", "call_id", "timestamp", "comment", "status", "reply", "replied_at"];

function toRow(entry: FeedbackEntry): Record<string, string> {
  return {
    id: entry.id,
    call_id: entry.callId,
    timestamp: entry.timestamp,
    comment: entry.comment,
    status: entry.status,
    reply: entry.reply,
    replied_at: entry.repliedAt
  };
}

function fromRow(headers: string[], row: string[]): FeedbackEntry {
  const get = (name: string) => {
    const index = headers.indexOf(name);
    return index >= 0 && index < row.length ? row[index] : "";
  };

  return {
    id: get("id"),
    callId: get("call_id"),
    timestamp: get("timestamp"),
    comment: get("comment"),
    status: (get("status") || "open") as FeedbackStatus,
    reply: get("reply"),
    repliedAt: get("replied_at")
  };
}

export class FeedbackRepository {
  constructor(private client: SheetsWriteClient) {}

  async addFeedback(callId: string, comment: string): Promise<FeedbackEntry> {
    const entry: FeedbackEntry = {
      id: randomUUID(),
      callId,
      timestamp: new Date().toISOString(),
      comment,
      status: "open",
      reply: "",
      repliedAt: ""
    };
    const headers = await this.client.getHeaders(TAB);

    await this.client.appendRow(TAB, headers.length > 0 ? headers : HEADERS, toRow(entry));
    return entry;
  }

  async addReply(feedbackId: string, reply: string): Promise<boolean> {
    const rowNumber = await this.client.findRowNumberById(TAB, "id", feedbackId);

    if (rowNumber === null) {
      return false;
    }

    const headers = await this.client.getHeaders(TAB);
    const existingRow = await this.client.getRow(TAB, rowNumber);
    const existing = fromRow(headers, existingRow);
    const updated: FeedbackEntry = {
      ...existing,
      reply,
      repliedAt: new Date().toISOString(),
      status: "resuelto"
    };

    await this.client.updateRow(TAB, rowNumber, headers.length > 0 ? headers : HEADERS, toRow(updated));
    return true;
  }

  async getFeedbackForCall(callId: string): Promise<FeedbackEntry[]> {
    const { headers, rows } = await this.client.getAllRows(TAB);

    return rows.map((row) => fromRow(headers, row)).filter((entry) => entry.callId === callId);
  }
}
