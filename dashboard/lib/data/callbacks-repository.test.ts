import { describe, expect, it } from "vitest";
import { CallbacksRepository } from "./callbacks-repository";
import { FakeSheetsWriteClient } from "./test-helpers/fake-sheets-write-client";

const HEADERS = [
  "Timestamp",
  "Status",
  "Full Name",
  "Phone Number",
  "Reason for Call",
  "Preferred Callback Time",
  "Email (optional)",
  "Call Id"
];

const EMERGENCY_HEADERS = [...HEADERS, "Comments"];

describe("CallbacksRepository.listCallbacks", () => {
  it("maps Emergency rows by header name", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Emergency", EMERGENCY_HEADERS, [
      [
        "2026-07-14 8:00",
        "Pending",
        "Jane Doe",
        "16035551234",
        "water leak",
        "Morning",
        "jane@example.com",
        "call_abc",
        "note"
      ]
    ]);
    const repo = new CallbacksRepository(client);

    const entries = await repo.listCallbacks("emergency");

    expect(entries).toEqual([
      {
        timestamp: "2026-07-14 8:00",
        status: "Pending",
        fullName: "Jane Doe",
        phoneNumber: "16035551234",
        reasonForCall: "water leak",
        preferredCallbackTime: "Morning",
        email: "jane@example.com",
        callId: "call_abc"
      }
    ]);
  });

  it("maps Non-Emergency rows (kind='general') from the 'Non-Emergency' tab", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Non-Emergency", HEADERS, [
      ["2026-07-14 9:00", "Pending", "John Smith", "16035550000", "quote follow-up", "Anytime", "", "call_xyz"]
    ]);
    const repo = new CallbacksRepository(client);

    const entries = await repo.listCallbacks("general");

    expect(entries[0].fullName).toBe("John Smith");
    expect(entries[0].email).toBe("");
  });
});

describe("CallbacksRepository.markReviewed", () => {
  it("sets Status to Reviewed and preserves every other column, including Comments", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Emergency", EMERGENCY_HEADERS, [
      [
        "2026-07-14 8:00",
        "Pending",
        "Jane Doe",
        "16035551234",
        "water leak",
        "Morning",
        "jane@example.com",
        "call_abc",
        "keep me"
      ]
    ]);
    const repo = new CallbacksRepository(client);

    const ok = await repo.markReviewed("emergency", "call_abc");

    expect(ok).toBe(true);
    const entries = await repo.listCallbacks("emergency");
    expect(entries[0].status).toBe("Reviewed");
    expect(entries[0].fullName).toBe("Jane Doe");
    const raw = await client.getRow("Emergency", 2);
    expect(raw[8]).toBe("keep me");
  });

  it("returns false when the call id doesn't exist in that tab", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Emergency", EMERGENCY_HEADERS, []);
    const repo = new CallbacksRepository(client);

    expect(await repo.markReviewed("emergency", "call_nope")).toBe(false);
  });
});

describe("CallbacksRepository.countPending", () => {
  it("counts empty and 'Pending' status as pending, everything else as not", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Non-Emergency", HEADERS, [
      ["t1", "Pending", "A", "1", "r", "c", "", "call_1"],
      ["t2", "", "B", "2", "r", "c", "", "call_2"],
      ["t3", "Reviewed", "C", "3", "r", "c", "", "call_3"],
      ["t4", "Completed", "D", "4", "r", "c", "", "call_4"]
    ]);
    const repo = new CallbacksRepository(client);

    expect(await repo.countPending("general")).toBe(2);
  });
});
