import type { NextConfig } from 'next';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Single source of truth for config: the repo-root `.env` (the same file the
// Python agent reads). Next.js only auto-loads env from the `frontend/` folder,
// so we load the root `.env` here as a FALLBACK — any variable already present
// in the environment (or in a local `frontend/.env.local`, if you keep one)
// still wins. This is why a teammate needs only the one root `.env`.
// See the README, "2. Configure (one .env)".
try {
  const rootEnv = resolve(process.cwd(), '..', '.env');
  for (const line of readFileSync(rootEnv, 'utf8').split('\n')) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (match && process.env[match[1]] === undefined) {
      process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
    }
  }
} catch {
  // No repo-root `.env` (e.g. CI or a deployed environment) — rely on the
  // ambient environment / a local frontend/.env.local instead.
}

const nextConfig: NextConfig = {};

export default nextConfig;
