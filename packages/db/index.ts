import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as schema from "./schema";
import * as dotenv from "dotenv";
import * as path from "path";

// Load from root if exists, but for packages/db we might have a specific one
dotenv.config({ path: path.join(__dirname, "../../.env") });

const databaseUrl = process.env.DATABASE_URL || "file:./local.db";

export const client = createClient({
  url: databaseUrl,
});

export const db = drizzle(client, { schema });
export * from "./schema";
