import bcrypt from "bcryptjs";

export async function verifyPassword(plainPassword: string, hash: string): Promise<boolean> {
  if (!hash) {
    return false;
  }

  return bcrypt.compare(plainPassword, hash);
}
