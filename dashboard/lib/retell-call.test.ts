import { describe, expect, it } from "vitest";
import { extractTranscriptTurns, pickRecordingUrl } from "./retell-call";

describe("pickRecordingUrl", () => {
  it("prioritizes the standard recording url", () => {
    expect(
      pickRecordingUrl({
        recording_url: "https://retell.example.com/recording.wav",
        scrubbed_recording_url: "https://retell.example.com/scrubbed.wav"
      })
    ).toBe("https://retell.example.com/recording.wav");
  });

  it("falls back to scrubbed or multichannel urls", () => {
    expect(
      pickRecordingUrl({
        recording_url: "",
        scrubbed_recording_url: "https://retell.example.com/scrubbed.wav"
      })
    ).toBe("https://retell.example.com/scrubbed.wav");
  });
});

describe("extractTranscriptTurns", () => {
  it("keeps only agent and user turns with content", () => {
    expect(
      extractTranscriptTurns({
        transcript_with_tool_calls: [
          { role: "agent", content: "Hello there" },
          { role: "tool_call_invocation", content: "{\"tool\":\"x\"}" },
          { role: "user", content: "Need help" },
          { role: "user", content: "   " }
        ]
      })
    ).toEqual([
      { role: "agent", content: "Hello there" },
      { role: "user", content: "Need help" }
    ]);
  });

  it("falls back to transcript_object when needed", () => {
    expect(
      extractTranscriptTurns({
        transcript_object: [{ role: "user", content: "Fallback transcript" }]
      })
    ).toEqual([{ role: "user", content: "Fallback transcript" }]);
  });
});
