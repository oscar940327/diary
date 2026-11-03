import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { getPlatformProxy, unstable_readConfig as readConfig } from 'wrangler';

// 用真正的 Wrangler 載入設定；秘密檔只在暫存目錄建立假資料。
describe('Local and deployment environment isolation', () => {
  let directory: string;

  beforeEach(() => { directory = mkdtempSync(join(tmpdir(), 'diary-environments-')); });
  afterEach(() => rmSync(directory, { recursive: true, force: true }));

  function copyConfig(environment: string) {
    const target = join(directory, 'environments', environment);
    mkdirSync(target, { recursive: true });
    const config = readFileSync(`environments/${environment}/wrangler.jsonc`, 'utf8');
    writeFileSync(join(target, 'wrangler.jsonc'), config);
    return target;
  }

  it('uses different Worker names and keeps tokens out of both Worker configurations', () => {
    const test = readConfig({ config: 'environments/test/wrangler.jsonc' });
    const production = readConfig({ config: 'environments/production/wrangler.jsonc' });

    expect(test.name).toBe('diary-test');
    expect(production.name).toBe('diary-production');
    expect(test.main).toBe(production.main);
    expect(test.vars).not.toHaveProperty('DISCORD_BOT_TOKEN');
    expect(production.vars).not.toHaveProperty('DISCORD_BOT_TOKEN');
  });

  it.each(['test', 'production'])('loads only the %s directory and never falls back to sibling/root vars', async (environment) => {
    const target = copyConfig(environment);
    const sibling = copyConfig(environment === 'test' ? 'production' : 'test');
    writeFileSync(join(directory, '.dev.vars'), 'DISCORD_APPLICATION_ID=root-value\nDISCORD_BOT_TOKEN=root-token');
    writeFileSync(join(sibling, '.dev.vars'), 'DISCORD_APPLICATION_ID=sibling-value\nDISCORD_BOT_TOKEN=sibling-token');
    // 選定環境刻意缺少應用程式 ID，不能從其他目錄補齊。
    writeFileSync(join(target, '.dev.vars'), 'DISCORD_OWNER_ID=333333333333333333');
    const proxy = await getPlatformProxy({ configPath: join(target, 'wrangler.jsonc'), persist: false, remoteBindings: false });

    try {
      expect(proxy.env.DISCORD_OWNER_ID).toBe('333333333333333333');
      expect(proxy.env).not.toHaveProperty('DISCORD_APPLICATION_ID');
      expect(proxy.env).not.toHaveProperty('DISCORD_BOT_TOKEN');
    } finally {
      await proxy.dispose();
    }
  });

  it.each(['test', 'production'])('missing %s vars do not load sibling/root settings', async (environment) => {
    const target = copyConfig(environment);
    const sibling = copyConfig(environment === 'test' ? 'production' : 'test');
    writeFileSync(join(directory, '.dev.vars'), 'DISCORD_APPLICATION_ID=root-value');
    writeFileSync(join(sibling, '.dev.vars'), 'DISCORD_APPLICATION_ID=sibling-value');
    const proxy = await getPlatformProxy({ configPath: join(target, 'wrangler.jsonc'), persist: false, remoteBindings: false });

    try {
      expect(proxy.env).not.toHaveProperty('DISCORD_APPLICATION_ID');
    } finally {
      await proxy.dispose();
    }
  });

  it('ignores all local secrets while keeping placeholder examples visible to git', () => {
    const files = [
      '.env.registration', '.dev.vars',
      'environments/test/.dev.vars', 'environments/production/.dev.vars',
    ];
    const ignored = execFileSync('git', ['check-ignore', '--stdin'], { input: files.join('\n'), encoding: 'utf8' });
    expect(ignored.trim().split('\n')).toEqual(files);
    for (const file of [
      '.env.registration.example', '.dev.vars.example',
      'environments/test/.dev.vars.example', 'environments/production/.dev.vars.example',
    ]) {
      expect(spawnSync('git', ['check-ignore', '--no-index', file]).status).toBe(1);
      expect(readFileSync(file, 'utf8')).not.toContain('DISCORD_BOT_TOKEN=');
    }
  });

  it('runs the real Node CLI in dry run mode without exposing tokens', () => {
    const result = spawnSync(process.execPath, [
      resolve('scripts/register-ping.ts'), '--env', 'test', '--dry-run',
    ], {
      env: {
        DISCORD_TEST_APPLICATION_ID: '111111111111111111',
        DISCORD_TEST_GUILD_ID: '444444444444444444',
        DISCORD_TEST_BOT_TOKEN: 'fake-cli-token',
      },
      encoding: 'utf8',
    });

    expect(result.status).toBe(0);
    expect(JSON.parse(result.stdout)).toMatchObject({ environment: 'test', dryRun: true });
    expect(result.stdout + result.stderr).not.toContain('fake-cli-token');
  });

  it('exits with a generic error for missing CLI arguments without printing a stack or token', () => {
    const result = spawnSync(process.execPath, [resolve('scripts/register-ping.ts')], {
      env: { DISCORD_TEST_BOT_TOKEN: 'fake-cli-token' }, encoding: 'utf8',
    });

    expect(result.status).toBe(1);
    expect(result.stderr).toContain('參數');
    expect(result.stderr).not.toContain('fake-cli-token');
    expect(result.stderr).not.toContain('at runRegistration');
  });
});
