import { describe, expect, it } from "vitest";
import { isPublicPath } from "./route-guard";

describe("isPublicPath", () => {
  it("login y api/login son publicas", () => {
    expect(isPublicPath("/login")).toBe(true);
    expect(isPublicPath("/api/login")).toBe(true);
  });

  it("assets de next son publicos", () => {
    expect(isPublicPath("/_next/static/chunk.js")).toBe(true);
  });

  it("el resto de las rutas no son publicas", () => {
    expect(isPublicPath("/")).toBe(false);
    expect(isPublicPath("/llamadas")).toBe(false);
    expect(isPublicPath("/llamadas/call_1")).toBe(false);
  });
});
