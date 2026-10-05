const publicApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// NEXT_PUBLIC_API_URL is the API as the browser reaches it. Server-side
// rendering can need a different address: inside the docker-compose `web`
// container, `localhost` is the container itself, so it reaches the API at
// API_INTERNAL_URL (http://api:8000) instead. Unset means "same as the
// browser", which is right for a native `npm run dev`.
export const apiBaseUrl =
  typeof window === "undefined"
    ? (process.env.API_INTERNAL_URL ?? publicApiUrl)
    : publicApiUrl;
