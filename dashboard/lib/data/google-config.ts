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

export function getGoogleSheetsConfig(): GoogleSheetsConfig | null {
  const serviceAccount = parseServiceAccountJson(process.env.GOOGLE_SERVICE_ACCOUNT_JSON ?? "");
  const spreadsheetId = process.env.GOOGLE_SHEET_ID ?? "";

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

  return {
    serviceAccountEmail,
    privateKey,
    spreadsheetId
  };
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
