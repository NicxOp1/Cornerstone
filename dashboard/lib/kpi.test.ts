import { describe, expect, it } from "vitest";
import { deltaBadge } from "./kpi";

describe("deltaBadge", () => {
  it("uses a friendlier label when there is no prior window", () => {
    expect(deltaBadge(null, true)).toEqual({
      label: "First window",
      tone: "neutral"
    });
  });
});
