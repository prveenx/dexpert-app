import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@dexpert/ui", "@dexpert/types"],
};

export default nextConfig;
