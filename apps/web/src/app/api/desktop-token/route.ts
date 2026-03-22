import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import jwt from "jsonwebtoken";

export async function GET(req: Request) {
  const session = await auth.api.getSession({
    headers: await headers()
  });

  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Create a JWT for the desktop app specifically since it needs to store it in keychain
  const token = jwt.sign(
    { sub: session.user.id, email: session.user.email, name: session.user.name },
    process.env.BETTER_AUTH_SECRET || "supersecretbetterauthsecret",
    { expiresIn: "30d" }
  );

  return NextResponse.json({ token });
}
