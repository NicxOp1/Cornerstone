export type CallbackKind = "emergency" | "general";

export interface CallbackEntry {
  callId: string;
  timestamp: string;
  status: string;
  fullName: string;
  phoneNumber: string;
  reasonForCall: string;
  preferredCallbackTime: string;
  email: string;
}

export function isCallbackPending(status: string): boolean {
  const value = status.trim().toLowerCase();
  return value === "" || value === "pending";
}
