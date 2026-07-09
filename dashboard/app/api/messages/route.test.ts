import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/data/sheets-writer", () => ({ buildWriteClient: vi.fn() }));
vi.mock("next/cache", () => ({ revalidateTag: vi.fn() }));
vi.mock("@/lib/data/messages-repository", () => ({
  MessagesRepository: vi.fn().mockImplementation(() => ({
    addMessage: vi.fn().mockResolvedValue({
      id: "msg_1",
      timestamp: "2026-07-08T00:00:00.000Z",
      sender: "john",
      text: "hola",
      readByEquipo: false,
      readByJohn: true
    })
  }))
}));

function buildRequest(body: unknown) {
  return new NextRequest("http://localhost/api/messages", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" }
  });
}

describe("POST /api/messages", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("crea el mensaje y devuelve 201", async () => {
    const { POST } = await import("./route");
    const response = await POST(buildRequest({ text: "hola", sender: "john" }));

    expect(response.status).toBe(201);
  });

  it("400 si falta text", async () => {
    const { POST } = await import("./route");
    const response = await POST(buildRequest({ sender: "john" }));

    expect(response.status).toBe(400);
  });

  it("invalida la tag messages, no calls ni summary", async () => {
    const { revalidateTag } = await import("next/cache");
    const { POST } = await import("./route");

    await POST(buildRequest({ text: "hola", sender: "john" }));

    expect(revalidateTag).toHaveBeenCalledWith("messages");
    expect(revalidateTag).not.toHaveBeenCalledWith("calls");
    expect(revalidateTag).not.toHaveBeenCalledWith("summary");
  });
});
