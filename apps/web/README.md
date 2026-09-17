# The Shatranj Heritage — Web

Next.js (App Router, TypeScript) frontend for The Shatranj Heritage.

See the [repository README](../../README.md#local-development) for setup instructions (Docker Compose or running natively), and [docs/Implementation Plan.md](../../docs/Implementation%20Plan.md) for what this app currently does and doesn't implement yet.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the dev server with hot reload |
| `npm run build` | Production build (standalone output, for Docker) |
| `npm run lint` | ESLint |
| `npm run typecheck` | Regenerate Next.js route types, then `tsc --noEmit` |
| `npm run format` / `format:write` | Prettier check / write |
