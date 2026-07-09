import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearAttempts, isRateLimited, recordFailedAttempt } from "./rate-limit";

describe("rate limiting de login", () => {
  beforeEach(() => {
    clearAttempts("1.2.3.4");
    vi.useRealTimers();
  });

  it("no bloquea con cero intentos", () => {
    expect(isRateLimited("1.2.3.4")).toBe(false);
  });

  it("bloquea despues de 5 intentos fallidos", () => {
    for (let i = 0; i < 5; i += 1) {
      recordFailedAttempt("1.2.3.4");
    }

    expect(isRateLimited("1.2.3.4")).toBe(true);
  });

  it("no bloquea con 4 intentos", () => {
    for (let i = 0; i < 4; i += 1) {
      recordFailedAttempt("1.2.3.4");
    }

    expect(isRateLimited("1.2.3.4")).toBe(false);
  });

  it("ips distintas no se contaminan entre si", () => {
    for (let i = 0; i < 5; i += 1) {
      recordFailedAttempt("1.2.3.4");
    }

    expect(isRateLimited("5.6.7.8")).toBe(false);
  });

  it("clearAttempts resetea el contador", () => {
    for (let i = 0; i < 5; i += 1) {
      recordFailedAttempt("1.2.3.4");
    }

    clearAttempts("1.2.3.4");

    expect(isRateLimited("1.2.3.4")).toBe(false);
  });
});
