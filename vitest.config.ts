import { cloudflareTest } from '@cloudflare/vitest-plugin';
import { defineConfig } from 'vitest/config';

// HTTP 行為在 Workers 測試；操作工具在 Node.js 測試。
export default defineConfig({
  test: {
    projects: [
      {
        plugins: [cloudflareTest({ wrangler: { configPath: './wrangler.jsonc' } })],
        test: { name: 'workers', include: ['tests/*.test.ts'] },
      },
      {
        test: { name: 'tools', include: ['tests/tooling/**/*.test.ts'], environment: 'node' },
      },
    ],
  },
});
