import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { runRegistration } from '../../scripts/register-ping';

// 只攔截外部 HTTP，設定與指令參數仍交給真正的工具入口處理。
describe('Discord ping registration tool', () => {
  const env = {
    DISCORD_TEST_APPLICATION_ID: '111111111111111111',
    DISCORD_TEST_GUILD_ID: '333333333333333333',
    DISCORD_TEST_BOT_TOKEN: 'fake-test-token',
    DISCORD_PRODUCTION_APPLICATION_ID: '222222222222222222',
    DISCORD_PRODUCTION_GUILD_ID: '444444444444444444',
    DISCORD_PRODUCTION_BOT_TOKEN: 'fake-production-token',
  };
  let http: ReturnType<typeof vi.spyOn<typeof globalThis, 'fetch'>>;

  beforeEach(() => {
    http = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 201 }));
  });

  afterEach(() => vi.restoreAllMocks());

  it.each([
    { args: [] }, { args: ['--dry-run'] }, { args: ['--env'] }, { args: ['--env', 'other'] },
    { args: ['--env', 'test', '--env', 'production'] }, { args: ['--env', 'test', '--unknown'] },
  ])('requires exactly one supported environment: $args', async ({ args }) => {
    await expect(runRegistration(args, env)).rejects.toThrow('參數');
    expect(http).not.toHaveBeenCalled();
  });

  it.each(['APPLICATION_ID', 'GUILD_ID', 'BOT_TOKEN'])(
    'does not fall back to production when test %s is missing', async (setting) => {
      const missing: Record<string, string | undefined> = { ...env };
      delete missing[`DISCORD_TEST_${setting}`];

      await expect(runRegistration(['--env', 'test'], missing)).rejects.toThrow('環境設定');
      expect(http).not.toHaveBeenCalled();
    },
  );

  it('does not fall back to test or unprefixed settings for production', async () => {
    const missing: Record<string, string | undefined> = {
      ...env, DISCORD_APPLICATION_ID: env.DISCORD_TEST_APPLICATION_ID,
      DISCORD_GUILD_ID: env.DISCORD_TEST_GUILD_ID, DISCORD_BOT_TOKEN: env.DISCORD_TEST_BOT_TOKEN,
    };
    delete missing.DISCORD_PRODUCTION_APPLICATION_ID;

    await expect(runRegistration(['--env', 'production'], missing)).rejects.toThrow('環境設定');
    expect(http).not.toHaveBeenCalled();
  });

  it.each([
    ['DISCORD_TEST_APPLICATION_ID', ''], ['DISCORD_TEST_APPLICATION_ID', 'not-an-id'],
    ['DISCORD_TEST_GUILD_ID', '333/commands'], ['DISCORD_TEST_BOT_TOKEN', ''],
    ['DISCORD_TEST_BOT_TOKEN', 'invalid token'],
  ])('rejects invalid configuration for %s', async (setting, value) => {
    await expect(runRegistration(['--env', 'test'], { ...env, [setting]: value }))
      .rejects.toThrow('環境設定');
    expect(http).not.toHaveBeenCalled();
  });

  it.each(['test', 'production'])('dry run shows the %s target without HTTP or token output', async (environment) => {
    const result = await runRegistration(['--env', environment, '--dry-run'], env);

    expect(result).toEqual({
      environment,
      applicationId: environment === 'test' ? '111111111111111111' : '222222222222222222',
      guildId: environment === 'test' ? '333333333333333333' : '444444444444444444',
      command: 'ping', dryRun: true,
    });
    expect(http).not.toHaveBeenCalled();
    expect(JSON.stringify(result)).not.toContain(env.DISCORD_TEST_BOT_TOKEN);
    expect(JSON.stringify(result)).not.toContain(env.DISCORD_PRODUCTION_BOT_TOKEN);
  });

  it.each([
    ['test', '111111111111111111', '333333333333333333', 'fake-test-token'],
    ['production', '222222222222222222', '444444444444444444', 'fake-production-token'],
  ])('only creates or updates the single ping command for %s', async (environment, application, guild, token) => {
    const result = await runRegistration(['--env', environment], env);

    expect(http).toHaveBeenCalledExactlyOnceWith(
      `https://discord.com/api/v10/applications/${application}/guilds/${guild}/commands`,
      {
        method: 'POST', redirect: 'error',
        headers: { Authorization: `Bot ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'ping', type: 1, description: '確認 Diary 後端連通' }),
      },
    );
    expect(result.dryRun).toBe(false);
    expect(JSON.stringify(result)).not.toContain(token);
  });

  it.each([200, 201])('accepts Discord create/update success status %s', async (status) => {
    http.mockResolvedValue(new Response('{}', { status }));

    await expect(runRegistration(['--env', 'test'], env)).resolves.toMatchObject({ dryRun: false });
  });

  it.each([401, 403, 429, 500])('reports HTTP %s without echoing the response body', async (status) => {
    http.mockResolvedValue(new Response(env.DISCORD_TEST_BOT_TOKEN, { status }));

    const output = await runRegistration(['--env', 'test'], env).catch(String);
    expect(output).toContain('註冊失敗');
    expect(output).toContain(String(status));
    expect(output).not.toContain(env.DISCORD_TEST_BOT_TOKEN);
  });

  it('does not expose tokens in network errors', async () => {
    http.mockRejectedValue(new Error(env.DISCORD_TEST_BOT_TOKEN));

    const output = await runRegistration(['--env', 'test'], env).catch(String);
    expect(output).toContain('註冊失敗');
    expect(output).not.toContain(env.DISCORD_TEST_BOT_TOKEN);
  });

  it.each(['APPLICATION_ID', 'BOT_TOKEN'])('rejects a shared %s between test and production', async (setting) => {
    await expect(runRegistration(['--env', 'test'], {
      ...env,
      [`DISCORD_PRODUCTION_${setting}`]: env[`DISCORD_TEST_${setting}` as keyof typeof env],
    })).rejects.toThrow('環境設定');
    expect(http).not.toHaveBeenCalled();
  });
});
