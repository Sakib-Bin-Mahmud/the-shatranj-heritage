import type { NextConfig } from "next";

// Product/category photography comes back from the API as absolute URLs
// hosted wherever S3_ENDPOINT_URL (apps/api) points — MinIO locally, a
// real S3/CDN host in production. next/image's optimizer requires that
// host on an explicit allowlist at build time, so it's mirrored here as
// its own public env var rather than assumed.
const assetBaseUrl = new URL(
  process.env.NEXT_PUBLIC_ASSET_BASE_URL ?? "http://localhost:9000",
);

// Next's image optimizer refuses to fetch from a loopback/private host by
// default (SSRF hardening) — correct for a real deployment, but MinIO runs
// on localhost in local dev (see docker-compose.yml / apps/api's
// S3_ENDPOINT_URL default), so that guard would block every product image
// there. Only relax it when the configured asset host is itself
// loopback/private, which is exactly the condition the guard exists for —
// a production NEXT_PUBLIC_ASSET_BASE_URL pointing at a real S3/CDN host
// never trips this.
const LOOPBACK_OR_PRIVATE_HOST =
  /^(localhost|127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|::1)$/;
const isLocalAssetHost = LOOPBACK_OR_PRIVATE_HOST.test(assetBaseUrl.hostname);

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: assetBaseUrl.protocol.replace(":", "") as "http" | "https",
        hostname: assetBaseUrl.hostname,
        port: assetBaseUrl.port || undefined,
      },
    ],
    ...(isLocalAssetHost ? { dangerouslyAllowLocalIP: true } : {}),
  },
};

export default nextConfig;
