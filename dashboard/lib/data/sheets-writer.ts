import { google, sheets_v4 } from "googleapis";
import {
  getCallbacksSheetConfig,
  getGoogleSheetsConfig,
  warnAboutMissingGoogleSheetsConfig
} from "@/lib/data/google-config";

export interface SheetsWriteClient {
  getHeaders(tab: string): Promise<string[]>;
  getRow(tab: string, rowNumber: number): Promise<string[]>;
  findRowNumberById(tab: string, idColumnName: string, id: string): Promise<number | null>;
  appendRow(tab: string, headers: string[], row: Record<string, string>): Promise<void>;
  updateRow(
    tab: string,
    rowNumber: number,
    headers: string[],
    row: Record<string, string>
  ): Promise<void>;
  getAllRows(tab: string): Promise<{ headers: string[]; rows: string[][] }>;
}

export class InMemorySheetsWriteClient implements SheetsWriteClient {
  private tabs = new Map<string, string[][]>();

  constructor() {
    this.ensureTab("Feedback", ["id", "call_id", "timestamp", "comment", "status", "reply", "replied_at"]);
    this.ensureTab("Messages", ["id", "timestamp", "sender", "text", "read_by_equipo", "read_by_john"]);
  }

  private ensureTab(tab: string, headers: string[] = []): string[][] {
    const existing = this.tabs.get(tab);

    if (existing) {
      return existing;
    }

    const seeded = [headers];
    this.tabs.set(tab, seeded);
    return seeded;
  }

  async getHeaders(tab: string): Promise<string[]> {
    return this.ensureTab(tab)[0] ?? [];
  }

  async getRow(tab: string, rowNumber: number): Promise<string[]> {
    return this.ensureTab(tab)[rowNumber - 1] ?? [];
  }

  async findRowNumberById(tab: string, idColumnName: string, id: string): Promise<number | null> {
    const data = this.ensureTab(tab);
    const idColumnIndex = data[0].indexOf(idColumnName);

    if (idColumnIndex === -1) {
      return null;
    }

    for (let index = 1; index < data.length; index += 1) {
      if (data[index][idColumnIndex] === id) {
        return index + 1;
      }
    }

    return null;
  }

  async appendRow(tab: string, headers: string[], row: Record<string, string>): Promise<void> {
    const data = this.ensureTab(tab, headers);
    const effectiveHeaders = data[0].length > 0 ? data[0] : headers;

    if (data[0].length === 0) {
      data[0] = effectiveHeaders;
    }

    data.push(effectiveHeaders.map((header) => row[header] ?? ""));
  }

  async updateRow(
    tab: string,
    rowNumber: number,
    headers: string[],
    row: Record<string, string>
  ): Promise<void> {
    const data = this.ensureTab(tab, headers);
    const effectiveHeaders = data[0].length > 0 ? data[0] : headers;

    if (data[0].length === 0) {
      data[0] = effectiveHeaders;
    }

    data[rowNumber - 1] = effectiveHeaders.map((header) => row[header] ?? "");
  }

  async getAllRows(tab: string): Promise<{ headers: string[]; rows: string[][] }> {
    const data = this.ensureTab(tab);

    return {
      headers: data[0] ?? [],
      rows: data.slice(1).filter((row) => row.length > 0 && row[0])
    };
  }
}

export class GoogleSheetsWriteClient implements SheetsWriteClient {
  constructor(
    private sheets: sheets_v4.Sheets,
    private spreadsheetId: string
  ) {}

  async getHeaders(tab: string): Promise<string[]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!1:1`
    });

    return (response.data.values?.[0] as string[] | undefined) ?? [];
  }

  async getRow(tab: string, rowNumber: number): Promise<string[]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!${rowNumber}:${rowNumber}`
    });

    return (response.data.values?.[0] as string[] | undefined) ?? [];
  }

  async findRowNumberById(tab: string, idColumnName: string, id: string): Promise<number | null> {
    const headers = await this.getHeaders(tab);
    const idColumnIndex = headers.indexOf(idColumnName);

    if (idColumnIndex === -1) {
      return null;
    }

    const columnLetter = String.fromCharCode(65 + idColumnIndex);
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!${columnLetter}:${columnLetter}`
    });
    const values = (response.data.values as string[][] | undefined) ?? [];
    const rowIndex = values.findIndex((row, index) => index > 0 && row[0] === id);

    return rowIndex === -1 ? null : rowIndex + 1;
  }

  async appendRow(tab: string, headers: string[], row: Record<string, string>): Promise<void> {
    await this.sheets.spreadsheets.values.append({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!A:A`,
      valueInputOption: "RAW",
      requestBody: {
        values: [headers.map((header) => row[header] ?? "")]
      }
    });
  }

  async updateRow(
    tab: string,
    rowNumber: number,
    headers: string[],
    row: Record<string, string>
  ): Promise<void> {
    await this.sheets.spreadsheets.values.update({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!A${rowNumber}`,
      valueInputOption: "RAW",
      requestBody: {
        values: [headers.map((header) => row[header] ?? "")]
      }
    });
  }

  async getAllRows(tab: string): Promise<{ headers: string[]; rows: string[][] }> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!A1:Z10000`
    });
    const values = (response.data.values as string[][] | undefined) ?? [];

    if (values.length === 0) {
      return { headers: [], rows: [] };
    }

    const [headers, ...rows] = values;
    return {
      headers,
      rows: rows.filter((row) => row.length > 0 && row[0])
    };
  }
}

const fallbackWriteClient = new InMemorySheetsWriteClient();

export function buildWriteClient(): SheetsWriteClient {
  const config = getGoogleSheetsConfig();

  if (!config) {
    warnAboutMissingGoogleSheetsConfig("buildWriteClient");
    return fallbackWriteClient;
  }

  const auth = new google.auth.JWT({
    email: config.serviceAccountEmail,
    key: config.privateKey,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"]
  });
  const sheets = google.sheets({ version: "v4", auth });

  return new GoogleSheetsWriteClient(sheets, config.spreadsheetId);
}

export function buildCallbacksWriteClient(): SheetsWriteClient {
  const config = getCallbacksSheetConfig();

  if (!config) {
    warnAboutMissingGoogleSheetsConfig("buildCallbacksWriteClient");
    return fallbackWriteClient;
  }

  const auth = new google.auth.JWT({
    email: config.serviceAccountEmail,
    key: config.privateKey,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"]
  });
  const sheets = google.sheets({ version: "v4", auth });

  return new GoogleSheetsWriteClient(sheets, config.spreadsheetId);
}
