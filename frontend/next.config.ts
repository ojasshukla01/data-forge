import type { NextConfig } from "next";

/**
 * Put build output in node_modules/.cache to avoid OneDrive/sync folder
 * conflicts that cause ENOENT on .next (routes-manifest, webpack cache, etc.).
 */
const nextConfig: NextConfig = {
  distDir: "node_modules/.cache/next",
};

export default nextConfig;
