import type { SheetsWriteClient } from "@/lib/data/sheets-writer";
import { isCallbackPending, type CallbackEntry, type CallbackKind } from "@/lib/types/callback";

const TAB_BY_KIND: Record<CallbackKind, string> = {
  emergency: "Emergency",
  general: "Non-Emergency"
};

function fromRow(headers: string[], row: string[]): CallbackEntry {
  const get = (name: string): string => {
    const index = headers.indexOf(name);
    return index >= 0 && index < row.length ? row[index] : "";
  };

  return {
    timestamp: get("Timestamp"),
    status: get("Status"),
    fullName: get("Full Name"),
    phoneNumber: get("Phone Number"),
    reasonForCall: get("Reason for Call"),
    preferredCallbackTime: get("Preferred Callback Time"),
    email: get("Email (optional)"),
    callId: get("Call Id")
  };
}

export class CallbacksRepository {
  constructor(private client: SheetsWriteClient) {}

  async listCallbacks(kind: CallbackKind): Promise<CallbackEntry[]> {
    const tab = TAB_BY_KIND[kind];
    const { headers, rows } = await this.client.getAllRows(tab);
    return rows.map((row) => fromRow(headers, row));
  }

  async markReviewed(kind: CallbackKind, callId: string): Promise<boolean> {
    const tab = TAB_BY_KIND[kind];
    const headers = await this.client.getHeaders(tab);
    const statusIndex = headers.indexOf("Status");

    if (statusIndex === -1) {
      return false;
    }

    const rowNumber = await this.client.findRowNumberById(tab, "Call Id", callId);

    if (rowNumber === null) {
      return false;
    }

    const existingRow = await this.client.getRow(tab, rowNumber);
    const updatedRow = [...existingRow];

    while (updatedRow.length < headers.length) {
      updatedRow.push("");
    }
    updatedRow[statusIndex] = "Reviewed";

    const rowRecord: Record<string, string> = {};
    headers.forEach((header, index) => {
      rowRecord[header] = updatedRow[index] ?? "";
    });

    await this.client.updateRow(tab, rowNumber, headers, rowRecord);
    return true;
  }

  async countPending(kind: CallbackKind): Promise<number> {
    const entries = await this.listCallbacks(kind);
    return entries.filter((entry) => isCallbackPending(entry.status)).length;
  }
}
