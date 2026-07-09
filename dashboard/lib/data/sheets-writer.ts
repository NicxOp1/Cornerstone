import { google, sheets_v4 } from "googleapis";

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

export function buildWriteClient(): GoogleSheetsWriteClient {
  const serviceAccount = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON ?? "{}");
  const auth = new google.auth.JWT({
    email: serviceAccount.client_email,
    key: serviceAccount.private_key,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"]
  });
  const sheets = google.sheets({ version: "v4", auth });

  return new GoogleSheetsWriteClient(sheets, process.env.GOOGLE_SHEET_ID ?? "");
}
