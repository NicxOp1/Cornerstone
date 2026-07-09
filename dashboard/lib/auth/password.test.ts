import bcrypt from "bcryptjs";
import { describe, expect, it } from "vitest";
import { verifyPassword } from "./password";

describe("verifyPassword", () => {
  it("devuelve true con la contrasena correcta", async () => {
    const hash = await bcrypt.hash("correcthorse", 10);

    expect(await verifyPassword("correcthorse", hash)).toBe(true);
  });

  it("devuelve false con la contrasena incorrecta", async () => {
    const hash = await bcrypt.hash("correcthorse", 10);

    expect(await verifyPassword("wrongpassword", hash)).toBe(false);
  });

  it("devuelve false si el hash esta vacio", async () => {
    expect(await verifyPassword("anything", "")).toBe(false);
  });
});
