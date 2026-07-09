import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/data/sheets-writer", () => ({ buildWriteClient: vi.fn() }));
vi.mock("next/cache", () => ({ revalidateTag: vi.fn() }));

function buildRequest(body: unknown) {
  return new NextRequest("http://localhost/api/feedback/fb_1", {
    method: "PATCH",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" }
  });
}

describe("PATCH /api/feedback/[id]", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.doUnmock("@/lib/data/feedback-repository");
  });

  it("200 y revalida feedback cuando la respuesta se guarda", async () => {
    vi.doMock("@/lib/data/feedback-repository", () => ({
      FeedbackRepository: vi.fn().mockImplementation(() => ({
        addReply: vi.fn().mockResolvedValue(true)
      }))
    }));
    const { PATCH } = await import("./route");
    const { revalidateTag } = await import("next/cache");

    const response = await PATCH(buildRequest({ reply: "Ya lo revisamos." }), {
      params: { id: "fb_1" }
    });

    expect(response.status).toBe(200);
    expect(revalidateTag).toHaveBeenCalledWith("feedback");
  });

  it("404 si el feedback no existe", async () => {
    vi.doMock("@/lib/data/feedback-repository", () => ({
      FeedbackRepository: vi.fn().mockImplementation(() => ({
        addReply: vi.fn().mockResolvedValue(false)
      }))
    }));
    const { PATCH } = await import("./route");

    const response = await PATCH(buildRequest({ reply: "Ya lo revisamos." }), {
      params: { id: "no-existe" }
    });

    expect(response.status).toBe(404);
  });

  it("400 si falta reply", async () => {
    vi.doMock("@/lib/data/feedback-repository", () => ({
      FeedbackRepository: vi.fn().mockImplementation(() => ({
        addReply: vi.fn()
      }))
    }));
    const { PATCH } = await import("./route");

    const response = await PATCH(buildRequest({}), { params: { id: "fb_1" } });

    expect(response.status).toBe(400);
  });
});
