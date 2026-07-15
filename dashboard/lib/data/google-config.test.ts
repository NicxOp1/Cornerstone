import { afterEach, describe, expect, it } from "vitest";
import { getCallbacksSheetConfig, getGoogleSheetsConfig } from "./google-config";

const VALID_SERVICE_ACCOUNT = JSON.stringify({
  client_email: "svc@example.iam.gserviceaccount.com",
  private_key: "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----\n"
});

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

describe("getCallbacksSheetConfig", () => {
  it("returns null when CALLBACKS_SHEET_ID is missing", () => {
    process.env.GOOGLE_SERVICE_ACCOUNT_JSON = VALID_SERVICE_ACCOUNT;
    delete process.env.CALLBACKS_SHEET_ID;

    expect(getCallbacksSheetConfig()).toBeNull();
  });

  it("returns a config using CALLBACKS_SHEET_ID, not GOOGLE_SHEET_ID", () => {
    process.env.GOOGLE_SERVICE_ACCOUNT_JSON = VALID_SERVICE_ACCOUNT;
    process.env.GOOGLE_SHEET_ID = "main-sheet-id";
    process.env.CALLBACKS_SHEET_ID = "callbacks-sheet-id";

    const config = getCallbacksSheetConfig();

    expect(config?.spreadsheetId).toBe("callbacks-sheet-id");
    expect(config?.serviceAccountEmail).toBe("svc@example.iam.gserviceaccount.com");
  });

  it("getGoogleSheetsConfig keeps reading GOOGLE_SHEET_ID unaffected by this change", () => {
    process.env.GOOGLE_SERVICE_ACCOUNT_JSON = VALID_SERVICE_ACCOUNT;
    process.env.GOOGLE_SHEET_ID = "main-sheet-id";
    process.env.CALLBACKS_SHEET_ID = "callbacks-sheet-id";

    expect(getGoogleSheetsConfig()?.spreadsheetId).toBe("main-sheet-id");
  });
});
