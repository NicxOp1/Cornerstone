interface GoogleSheetsConfig {
  privateKey: string;
  serviceAccountEmail: string;
  spreadsheetId: string;
}

function parseServiceAccountJson(raw: string): Record<string, unknown> | null {
  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function buildConfig(spreadsheetId: string): GoogleSheetsConfig | null {
  const serviceAccount = parseServiceAccountJson(process.env.GOOGLE_SERVICE_ACCOUNT_JSON ?? "");

  if (!serviceAccount || !spreadsheetId.trim()) {
    return null;
  }

  const serviceAccountEmail =
    typeof serviceAccount.client_email === "string" ? serviceAccount.client_email : "";
  const privateKey =
    typeof serviceAccount.private_key === "string" ? serviceAccount.private_key : "";

  if (!serviceAccountEmail.trim() || !privateKey.trim()) {
    return null;
  }

  return { serviceAccountEmail, privateKey, spreadsheetId };
}

export function getGoogleSheetsConfig(): GoogleSheetsConfig | null {
  return buildConfig(process.env.GOOGLE_SHEET_ID ?? "");
}

export function getCallbacksSheetConfig(): GoogleSheetsConfig | null {
  return buildConfig(process.env.CALLBACKS_SHEET_ID ?? "");
}

let warned = false;

export function warnAboutMissingGoogleSheetsConfig(context: string): void {
  if (process.env.NODE_ENV === "production" || warned) {
    return;
  }

  warned = true;
  console.warn(
    `[dashboard] Missing Google Sheets config in ${context}. Falling back to local in-memory data.`
  );
}
