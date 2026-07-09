import { randomUUID } from "crypto";
import type { SheetsWriteClient } from "@/lib/data/sheets-writer";
import type { MessageEntry, MessageSender } from "@/lib/types/message";

const TAB = "Messages";
const HEADERS = ["id", "timestamp", "sender", "text", "read_by_equipo", "read_by_john"];

function toRow(entry: MessageEntry): Record<string, string> {
  return {
    id: entry.id,
    timestamp: entry.timestamp,
    sender: entry.sender,
    text: entry.text,
    read_by_equipo: String(entry.readByEquipo),
    read_by_john: String(entry.readByJohn)
  };
}

function fromRow(headers: string[], row: string[]): MessageEntry {
  const get = (name: string) => {
    const index = headers.indexOf(name);
    return index >= 0 && index < row.length ? row[index] : "";
  };

  return {
    id: get("id"),
    timestamp: get("timestamp"),
    sender: (get("sender") || "john") as MessageSender,
    text: get("text"),
    readByEquipo: get("read_by_equipo") === "true",
    readByJohn: get("read_by_john") === "true"
  };
}

export class MessagesRepository {
  constructor(private client: SheetsWriteClient) {}

  async addMessage(sender: MessageSender, text: string): Promise<MessageEntry> {
    const entry: MessageEntry = {
      id: randomUUID(),
      timestamp: new Date().toISOString(),
      sender,
      text,
      readByEquipo: sender === "equipo",
      readByJohn: sender === "john"
    };
    const headers = await this.client.getHeaders(TAB);

    await this.client.appendRow(TAB, headers.length > 0 ? headers : HEADERS, toRow(entry));
    return entry;
  }

  async listMessages(): Promise<MessageEntry[]> {
    const { headers, rows } = await this.client.getAllRows(TAB);
    return rows.map((row) => fromRow(headers, row));
  }

  async countUnreadForEquipo(): Promise<number> {
    const messages = await this.listMessages();
    return messages.filter((message) => !message.readByEquipo).length;
  }

  async markAllReadByEquipo(): Promise<void> {
    const { headers, rows } = await this.client.getAllRows(TAB);
    const writeHeaders = headers.length > 0 ? headers : HEADERS;

    for (let index = 0; index < rows.length; index += 1) {
      const entry = fromRow(headers, rows[index]);

      if (!entry.readByEquipo) {
        const updated: MessageEntry = {
          ...entry,
          readByEquipo: true
        };

        await this.client.updateRow(TAB, index + 2, writeHeaders, toRow(updated));
      }
    }
  }
}
