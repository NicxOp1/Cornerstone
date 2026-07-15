import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/retell-call", () => ({
  RetellCallError: class RetellCallError extends Error {
    status: number;

    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
  extractTranscriptTurns: vi.fn(),
  fetchRetellCall: vi.fn()
}));

describe("GET /api/calls/[callId]/transcript", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("returns transcript turns from Retell", async () => {
    const retell = await import("@/lib/retell-call");
    vi.mocked(retell.fetchRetellCall).mockResolvedValue({});
    vi.mocked(retell.extractTranscriptTurns).mockReturnValue([
      { role: "agent", content: "Hi" },
      { role: "user", content: "Hello" }
    ]);

    const { GET } = await import("./route");
    const response = await GET(new Request("http://localhost"), { params: { callId: "call_1" } });

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual([
      { role: "agent", content: "Hi" },
      { role: "user", content: "Hello" }
    ]);
  });

  it("surfaces Retell 404s", async () => {
    const retell = await import("@/lib/retell-call");
    vi.mocked(retell.fetchRetellCall).mockRejectedValue(new retell.RetellCallError(404, "not found"));

    const { GET } = await import("./route");
    const response = await GET(new Request("http://localhost"), { params: { callId: "call_1" } });

    expect(response.status).toBe(404);
  });
});
