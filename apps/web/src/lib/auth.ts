import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";
import * as schema from "./db-schema";

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: "sqlite",
    schema: {
      user: schema.users,
      session: schema.sessions,
      account: schema.accounts,
      verification: schema.verifications,
    },
  }),
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: true,
  },
  emailVerification: {
    sendOnSignUp: true,
    async sendVerificationEmail({ user, url, token }: { user: any, url: any, token: any }, request: any) {
      if (process.env.RESEND_API_KEY) {
        await fetch("https://api.resend.com/emails", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
          },
          body: JSON.stringify({
            from: "Dexpert <onboarding@resend.dev>",
            to: [user.email],
            subject: "Verify your email address",
            html: `<div><p>Click <a href="${url}">here</a> to verify your email.</p></div>`,
          }),
        });
      } else {
        console.log(`Email verification url for ${user.email}: ${url}`);
      }
    },
  },
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID as string,
      clientSecret: process.env.GITHUB_CLIENT_SECRET as string,
    },
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
    },
  },
  trustedOrigins: ["dexpert://", "http://localhost:5173", "http://localhost:3000"],
  secret: process.env.BETTER_AUTH_SECRET,
});
