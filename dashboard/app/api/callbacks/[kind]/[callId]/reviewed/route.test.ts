import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/data/sheets-writer", () => ({ buildCallbacksWriteClient: vi.fn() }));
vi.mock("next/cache", () => ({ revalidateTag: vi.fn() }));

function buildRequest() {
  return new NextRequest("http://localhost/api/callbacks/emergency/call_abc/reviewed", {
    method: "PATCH"
  });
}

describe("PATCH /api/callbacks/[kind]/[callId]/reviewed", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.doUnmock("@/lib/data/callbacks-repository");
  });

  it("200 y revalida callbacks cuando se marca revisado", async () => {
    const markReviewed = vi.fn().mockResolvedValue(true);
    vi.doMock("@/lib/data/callbacks-repository", () => ({
      CallbacksRepository: vi.fn().mockImplementation(() => ({ markReviewed }))
    }));
    const { PATCH } = await import("./route");
    const { revalidateTag } = await import("next/cache");

    const response = await PATCH(buildRequest(), { params: { kind: "emergency", callId: "call_abc" } });

    expect(response.status).toBe(200);
    expect(markReviewed).toHaveBeenCalledWith("emergency", "call_abc");
    expect(revalidateTag).toHaveBeenCalledWith("callbacks");
  });

  it("404 si el callback no existe", async () => {
    vi.doMock("@/lib/data/callbacks-repository", () => ({
      CallbacksRepository: vi.fn().mockImplementation(() => ({
        markReviewed: vi.fn().mockResolvedValue(false)
      }))
    }));
    const { PATCH } = await import("./route");

    const response = await PATCH(buildRequest(), { params: { kind: "emergency", callId: "call_missing" } });

    expect(response.status).toBe(404);
  });

  it("400 si kind no es 'emergency' ni 'general'", async () => {
    const markReviewed = vi.fn();
    vi.doMock("@/lib/data/callbacks-repository", () => ({
      CallbacksRepository: vi.fn().mockImplementation(() => ({ markReviewed }))
    }));
    const { PATCH } = await import("./route");

    const response = await PATCH(buildRequest(), { params: { kind: "bogus", callId: "call_abc" } });

    expect(response.status).toBe(400);
    expect(markReviewed).not.toHaveBeenCalled();
  });
});
