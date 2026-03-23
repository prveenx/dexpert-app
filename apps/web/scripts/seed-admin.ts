import { auth } from "../src/lib/auth";
import { db, users } from "@dexpert/db";
import { eq } from "drizzle-orm";

async function main() {
  const adminEmail = "admin@dexpert.com";
  const adminPassword = "admin@123";
  const adminName = "Admin User";

  console.log(`Ensuring admin user ${adminEmail}...`);

  // First, check if user exists. If so, delete it to ensure a clean state with correct hashing
  const existingUser = await db.query.users.findFirst({
    where: eq(users.email, adminEmail),
  });

  if (existingUser) {
    console.log("Admin user exists. Deleting to re-create with fresh hash...");
    // Better Auth handles cascading deletion in many cases, but we'll be safe
    // Since we're in dev, deleting and re-creating is the most reliable way 
    // to ensure the internal Better Auth hasher is used.
    
    // We'll use the DB directly to clear them out
    const { accounts, sessions } = await import("@dexpert/db");
    await db.delete(accounts).where(eq(accounts.userId, existingUser.id));
    await db.delete(sessions).where(eq(sessions.userId, existingUser.id));
    await db.delete(users).where(eq(users.id, existingUser.id));
  }

  console.log("Creating admin user via Better Auth API...");
  try {
    // This uses the EXACT hashing configuration Better Auth expects
    await auth.api.signUpEmail({
      body: {
        email: adminEmail,
        password: adminPassword,
        name: adminName,
      },
    });

    console.log("User created successfully!");

    // Update to Pro and verified
    await db.update(users)
      .set({ emailVerified: true, plan: "pro", credits: 999 })
      .where(eq(users.email, adminEmail));

    console.log("Admin user verified and upgraded!");
  } catch (error: any) {
    console.error("Failed to seed via API:", error.message || error);
    // If it fails with "User already exists" even after deletion (async lag?), we retry or skip
  }
}

main().then(() => {
    console.log("Seed complete.");
    process.exit(0);
}).catch((err) => {
    console.error(err);
    process.exit(1);
});
