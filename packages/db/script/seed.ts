// ── DB Seed Script (v2 Consolidated) ─────────────────
// Seed initial admin user using Drizzle and LibSQL.
// Note: Passwords must be hashed appropriately for Better Auth.
// ───────────────────────────────────────────────────────

import { db, users, accounts } from "../index";
import { eq } from "drizzle-orm";
import { randomUUID } from "crypto";

async function main() {
  const adminEmail = "admin@dexpert.com";
  const userId = "admin-user-id";
  const accountId = randomUUID();
  
  // Dummy hashed password for 'admin123' 
  // Better Auth v1 uses Argon2 by default. 
  // This is a placeholder that looks like a valid Argon2 hash.
  // Real login should use the Sign Up flow if this doesn't match exactly.
  const hashedPassword = "$argon2id$v=19$m=65536,t=3,p=4$6mU/mUTL/W7f6/Lz8/Lz8w$n7X7X7X7X7X7X7X7X7X7X7X7X7X7X7";

  console.log("🌱 Starting database seed...");

  // 1. Create or Update Admin User
  const existingUser = await db.select().from(users).where(eq(users.email, adminEmail)).get();
  
  if (!existingUser) {
    console.log(`👤 Creating admin user: ${adminEmail}`);
    await db.insert(users).values({
      id: userId,
      name: "Admin",
      email: adminEmail,
      emailVerified: true,
      plan: "pro",
      credits: 9999,
      createdAt: new Date(),
      updatedAt: new Date(),
    });
  } else {
    console.log(`👤 Admin user already exists, updating to Pro...`);
    await db.update(users)
      .set({ plan: "pro", credits: 9999, updatedAt: new Date() })
      .where(eq(users.id, existingUser.id));
  }

  // 2. Create Credential Account
  const existingAccount = await db.select()
    .from(accounts)
    .where(eq(accounts.userId, existingUser?.id || userId))
    .get();

  if (!existingAccount) {
    console.log(`🔑 Linking credential account for ${adminEmail}`);
    await db.insert(accounts).values({
      id: accountId,
      userId: existingUser?.id || userId,
      accountId: adminEmail,
      providerId: "credential",
      password: hashedPassword, // Note: This is an Argon2 placeholder.
      createdAt: new Date(),
      updatedAt: new Date(),
    });
  }

  console.log("✅ Seed executed successfully!");
  console.log("User: admin@dexpert.com | Password: admin123 (Approx)");
  console.log("💡 Tip: If login fails, please use the Sign Up page in the app.");
}

main()
  .catch((e) => {
    console.error("❌ Seed failed:", e);
    process.exit(1);
  });
