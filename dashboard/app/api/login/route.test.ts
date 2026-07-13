import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/password", () => ({ verifyPassword: vi.fn() }));
vi.mock("@/lib/auth/session", async () => {
  const actual = await vi.importActual<typeof import("@/lib/auth/session")>("@/lib/auth/session");
  return { ...actual, createSessionToken: vi.fn().mockResolvedValue("fake-token") };
});
vi.mock("@/lib/auth/rate-limit", () => ({
  isRateLimited: vi.fn().mockReturnValue(false),
  recordFailedAttempt: vi.fn(),
  clearAttempts: vi.fn()
}));

function buildRequest(body: unknown) {
  return new NextRequest("http://localhost/api/login", {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
      "x-forwarded-for": "1.2.3.4"
    }
  });
}

describe("POST /api/login", () => {
  beforeEach(() => {
    vi.stubEnv("DASHBOARD_USERNAME", "john");
    vi.stubEnv("DASHBOARD_PASSWORD", "hashed-password");
    vi.stubEnv("DASHBOARD_SECONDARY_USERNAME", "");
    vi.stubEnv("DASHBOARD_SECONDARY_PASSWORD", "");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("credenciales correctas devuelven 200 y setean la cookie de sesion", async () => {
    const { verifyPassword } = await import("@/lib/auth/password");
    vi.mocked(verifyPassword).mockResolvedValue(true);
    const { POST } = await import("./route");

    const response = await POST(buildRequest({ username: "john", password: "correcthorse" }));

    expect(response.status).toBe(200);
    expect(response.cookies.get("dashboard_session")?.value).toBe("fake-token");
  });

  it("usuario incorrecto devuelve 401", async () => {
    const { POST } = await import("./route");

    const response = await POST(buildRequest({ username: "otro", password: "cualquiera" }));

    expect(response.status).toBe(401);
  });

  it("credenciales secundarias correctas devuelven 200 y setean la cookie", async () => {
    vi.stubEnv("DASHBOARD_SECONDARY_USERNAME", "secondary-user");
    vi.stubEnv("DASHBOARD_SECONDARY_PASSWORD", "secondary-hash");
    const { verifyPassword } = await import("@/lib/auth/password");
    vi.mocked(verifyPassword).mockResolvedValue(true);
    const { POST } = await import("./route");

    const response = await POST(
      buildRequest({ username: "secondary-user", password: "secondary-pass" })
    );

    expect(response.status).toBe(200);
    expect(response.cookies.get("dashboard_session")?.value).toBe("fake-token");
    expect(verifyPassword).toHaveBeenCalledWith("secondary-pass", "secondary-hash");
  });

  it("contrasena incorrecta devuelve 401 y registra el intento fallido", async () => {
    const { verifyPassword } = await import("@/lib/auth/password");
    vi.mocked(verifyPassword).mockResolvedValue(false);
    const { recordFailedAttempt } = await import("@/lib/auth/rate-limit");
    const { POST } = await import("./route");

    const response = await POST(buildRequest({ username: "john", password: "mal" }));

    expect(response.status).toBe(401);
    expect(recordFailedAttempt).toHaveBeenCalledWith("1.2.3.4");
  });

  it("rate limit activo devuelve 429 sin llegar a verificar password", async () => {
    const { isRateLimited } = await import("@/lib/auth/rate-limit");
    vi.mocked(isRateLimited).mockReturnValue(true);
    const { verifyPassword } = await import("@/lib/auth/password");
    const { POST } = await import("./route");

    const response = await POST(buildRequest({ username: "john", password: "correcthorse" }));

    expect(response.status).toBe(429);
    expect(verifyPassword).not.toHaveBeenCalled();
  });
});
