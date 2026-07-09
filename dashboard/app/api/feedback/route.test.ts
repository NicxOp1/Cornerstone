import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/data/sheets-writer", () => ({ buildWriteClient: vi.fn() }));
vi.mock("next/cache", () => ({ revalidateTag: vi.fn() }));
vi.mock("@/lib/data/feedback-repository", () => ({
  FeedbackRepository: vi.fn().mockImplementation(() => ({
    addFeedback: vi.fn().mockResolvedValue({
      id: "fb_1",
      callId: "call_1",
      comment: "test",
      status: "open",
      reply: "",
      repliedAt: "",
      timestamp: "2026-07-08T00:00:00.000Z"
    })
  }))
}));

function buildRequest(body: unknown) {
  return new NextRequest("http://localhost/api/feedback", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" }
  });
}

describe("POST /api/feedback", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("crea el feedback y devuelve 201", async () => {
    const { POST } = await import("./route");
    const response = await POST(buildRequest({ callId: "call_1", comment: "test" }));

    expect(response.status).toBe(201);
  });

  it("400 si falta callId", async () => {
    const { POST } = await import("./route");
    const response = await POST(buildRequest({ comment: "test" }));

    expect(response.status).toBe(400);
  });

  it("400 si falta comment", async () => {
    const { POST } = await import("./route");
    const response = await POST(buildRequest({ callId: "call_1" }));

    expect(response.status).toBe(400);
  });

  it("invalida la tag feedback tras crear, no calls", async () => {
    const { revalidateTag } = await import("next/cache");
    const { POST } = await import("./route");

    await POST(buildRequest({ callId: "call_1", comment: "test" }));

    expect(revalidateTag).toHaveBeenCalledWith("feedback");
    expect(revalidateTag).not.toHaveBeenCalledWith("calls");
  });
});
