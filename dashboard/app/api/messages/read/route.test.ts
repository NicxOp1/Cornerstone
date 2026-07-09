import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/data/sheets-writer", () => ({ buildWriteClient: vi.fn() }));
vi.mock("next/cache", () => ({ revalidateTag: vi.fn() }));
vi.mock("@/lib/data/messages-repository", () => ({
  MessagesRepository: vi.fn().mockImplementation(() => ({
    markAllReadByEquipo: vi.fn().mockResolvedValue(undefined)
  }))
}));

describe("POST /api/messages/read", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("devuelve 200 y revalida la tag messages", async () => {
    const { POST } = await import("./route");
    const { revalidateTag } = await import("next/cache");

    const response = await POST();

    expect(response.status).toBe(200);
    expect(revalidateTag).toHaveBeenCalledWith("messages");
  });
});
