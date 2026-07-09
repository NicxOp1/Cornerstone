import { google, sheets_v4 } from "googleapis";
import { mapRowToCall } from "@/lib/data/call-mapper";
import type { CallFilters, CallsRepository, SummaryMetrics } from "@/lib/data/repository";
import { computeSummaryMetrics } from "@/lib/metrics";
import type { Call } from "@/lib/types/call";

const SHEET_RANGE = "Calls!A1:Z10000";

export interface SheetsValuesClient {
  getValues(range: string): Promise<string[][]>;
}

export class GoogleSheetsValuesClient implements SheetsValuesClient {
  constructor(
    private sheets: sheets_v4.Sheets,
    private spreadsheetId: string
  ) {}

  async getValues(range: string): Promise<string[][]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range
    });

    return (response.data.values as string[][] | undefined) ?? [];
  }
}

async function fetchAllCalls(client: SheetsValuesClient): Promise<Call[]> {
  const rows = await client.getValues(SHEET_RANGE);

  if (rows.length < 2) {
    return [];
  }

  const [headers, ...dataRows] = rows;

  return dataRows
    .filter((row) => row.length > 0 && row[0])
    .map((row) => mapRowToCall(headers, row));
}

export function applyFilters(calls: Call[], filters: CallFilters = {}): Call[] {
  return calls.filter((call) => {
    if (filters.dateFrom && call.day < filters.dateFrom) return false;
    if (filters.dateTo && call.day > filters.dateTo) return false;
    if (filters.sentiment && call.sentiment !== filters.sentiment) return false;
    if (filters.intent && call.intent !== filters.intent) return false;
    if (filters.serviceType && call.serviceType !== filters.serviceType) return false;
    if (
      filters.callSuccessful !== undefined &&
      call.callSuccessful !== filters.callSuccessful
    ) {
      return false;
    }

    return true;
  });
}

export class SheetsCallsRepository implements CallsRepository {
  constructor(private client: SheetsValuesClient) {}

  async getCalls(filters: CallFilters = {}): Promise<Call[]> {
    const calls = await fetchAllCalls(this.client);
    return applyFilters(calls, filters);
  }

  async getCallById(callId: string): Promise<Call | null> {
    const calls = await fetchAllCalls(this.client);
    return calls.find((call) => call.callId === callId) ?? null;
  }

  async getSummaryMetrics(): Promise<SummaryMetrics> {
    const calls = await fetchAllCalls(this.client);
    return computeSummaryMetrics(calls);
  }
}

export function buildProductionRepository(): SheetsCallsRepository {
  const serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON ?? "{}");
  const auth = new google.auth.JWT({
    email: serviceAccount.client_email,
    key: serviceAccount.private_key,
    scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"]
  });
  const sheets = google.sheets({ version: "v4", auth });
  const client = new GoogleSheetsValuesClient(sheets, process.env.GOOGLE_SHEET_ID ?? "");

  return new SheetsCallsRepository(client);
}
