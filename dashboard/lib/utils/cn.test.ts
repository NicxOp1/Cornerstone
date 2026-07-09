import { describe, expect, it } from "vitest";
import { cn } from "./cn";

describe("cn", () => {
  it("une clases verdaderas con un espacio", () => {
    expect(cn("a", "b", "c")).toBe("a b c");
  });

  it("filtra valores falsy", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });
});
