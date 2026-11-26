import { fileURLToPath, URL } from 'node:url';
import { cloudflareTest, readD1Migrations } from '@cloudflare/vitest-plugin';
import { defineConfig } from 'vitest/config';

const migrationsDir = fileURLToPath(new URL('./migrations', import.meta.url));

// HTTP 行為在 Workers 測試；操作工具在 Node.js 測試。
export default defineConfig({
  test: {
    projects: [
      {
        plugins: [cloudflareTest(async () => ({
          wrangler: { configPath: './wrangler.jsonc' },
          remoteBindings: false,
          miniflare: {
            bindings: { TEST_D1_MIGRATIONS: await readD1Migrations(migrationsDir) },
          },
        }))],
        test: { name: 'workers', include: ['tests/*.test.ts'] },
      },
      {
        test: { name: 'tools', include: ['tests/tooling/**/*.test.ts'], environment: 'node' },
      },
    ],
  },
});
