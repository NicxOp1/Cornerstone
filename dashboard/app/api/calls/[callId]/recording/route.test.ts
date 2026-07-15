import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/retell-call", () => ({
  RetellCallError: class RetellCallError extends Error {
    status: number;

    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
  fetchRetellCall: vi.fn(),
  pickRecordingUrl: vi.fn()
}));

describe("GET /api/calls/[callId]/recording", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("redirects to the Retell recording when available", async () => {
    const retell = await import("@/lib/retell-call");
    vi.mocked(retell.fetchRetellCall).mockResolvedValue({});
    vi.mocked(retell.pickRecordingUrl).mockReturnValue("https://retell.example.com/recording.wav");

    const { GET } = await import("./route");
    const response = await GET(new Request("http://localhost"), { params: { callId: "call_1" } });

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://retell.example.com/recording.wav");
  });

  it("returns 404 when the call has no recording url", async () => {
    const retell = await import("@/lib/retell-call");
    vi.mocked(retell.fetchRetellCall).mockResolvedValue({});
    vi.mocked(retell.pickRecordingUrl).mockReturnValue("");

    const { GET } = await import("./route");
    const response = await GET(new Request("http://localhost"), { params: { callId: "call_1" } });

    expect(response.status).toBe(404);
  });
});
