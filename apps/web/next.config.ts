import type { NextConfig } from "next";

// Product/category photography comes back from the API as absolute URLs
// under apps/api's S3_PUBLIC_BASE_URL (falling back to S3_ENDPOINT_URL) —
// MinIO locally, a real S3/CDN host in production. next/image's optimizer
// requires that host on an explicit allowlist at build time, so it's
// mirrored here as its own public env var rather than assumed.
const assetBaseUrl = new URL(
  process.env.NEXT_PUBLIC_ASSET_BASE_URL ?? "http://localhost:9000",
);

// A loopback/private asset host means local MinIO. The optimizer can't be
// relied on to fetch from it: inside the docker-compose `web` container,
// `localhost` is the container itself, not MinIO, so every image would
// 500. Skip optimization there and let the browser load MinIO directly —
// a production NEXT_PUBLIC_ASSET_BASE_URL pointing at a real S3/CDN host
// never trips this, so images are still optimized where it matters.
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
    ...(isLocalAssetHost ? { unoptimized: true } : {}),
  },
};

export default nextConfig;
