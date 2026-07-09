// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from "vitest";

describe("session tokens", () => {
  beforeEach(() => {
    vi.stubEnv("SESSION_SECRET", "test-secret-at-least-32-characters-long");
  });

  it("crea un token que se puede verificar de vuelta", async () => {
    const { createSessionToken, verifySessionToken } = await import("./session");

    const token = await createSessionToken("john");
    const session = await verifySessionToken(token);

    expect(session?.username).toBe("john");
  });

  it("rechaza un token invalido", async () => {
    const { verifySessionToken } = await import("./session");

    const session = await verifySessionToken("token-invalido-cualquiera");

    expect(session).toBeNull();
  });

  it("rechaza un token vacio", async () => {
    const { verifySessionToken } = await import("./session");

    const session = await verifySessionToken("");

    expect(session).toBeNull();
  });
});
