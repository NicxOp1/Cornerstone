import type { SheetsWriteClient } from "@/lib/data/sheets-writer";

export class FakeSheetsWriteClient implements SheetsWriteClient {
  private tabs = new Map<string, string[][]>();

  seed(tab: string, headers: string[], rows: string[][] = []) {
    this.tabs.set(tab, [headers, ...rows]);
  }

  private data(tab: string): string[][] {
    const existing = this.tabs.get(tab);

    if (!existing) {
      throw new Error(`Tab '${tab}' no fue sembrada con seed() antes de usarla en el test`);
    }

    return existing;
  }

  async getHeaders(tab: string): Promise<string[]> {
    return this.data(tab)[0];
  }

  async getRow(tab: string, rowNumber: number): Promise<string[]> {
    return this.data(tab)[rowNumber - 1] ?? [];
  }

  async findRowNumberById(tab: string, idColumnName: string, id: string): Promise<number | null> {
    const data = this.data(tab);
    const idColumnIndex = data[0].indexOf(idColumnName);

    for (let index = 1; index < data.length; index += 1) {
      if (data[index][idColumnIndex] === id) {
        return index + 1;
      }
    }

    return null;
  }

  async appendRow(tab: string, headers: string[], row: Record<string, string>): Promise<void> {
    this.data(tab).push(headers.map((header) => row[header] ?? ""));
  }

  async updateRow(
    tab: string,
    rowNumber: number,
    headers: string[],
    row: Record<string, string>
  ): Promise<void> {
    this.data(tab)[rowNumber - 1] = headers.map((header) => row[header] ?? "");
  }

  async getAllRows(tab: string): Promise<{ headers: string[]; rows: string[][] }> {
    const data = this.data(tab);

    return {
      headers: data[0],
      rows: data.slice(1).filter((row) => row.length > 0 && row[0])
    };
  }
}
