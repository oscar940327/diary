import { beforeAll, describe, expect, it, vi } from 'vitest';
import worker from '../src/index';
import { createDiscordFixture } from './helpers/discord';

// 透過已簽署請求，驗證授權與私人指令回覆。
describe('Owner-only Discord commands', () => {
  let discord: Awaited<ReturnType<typeof createDiscordFixture>>;

  beforeAll(async () => {
    discord = await createDiscordFixture();
  });

  // 預設為擁有者的合法 /ping，各案例只覆寫要驗證的欄位。
  function command(overrides: Record<string, unknown> = {}) {
    return {
      application_id: discord.bindings.DISCORD_APPLICATION_ID,
      type: 2,
      guild_id: discord.bindings.DISCORD_GUILD_ID,
      member: { user: { id: discord.bindings.DISCORD_OWNER_ID } },
      data: { id: '456789012345678901', name: 'ping', type: 1 },
      ...overrides,
    };
  }

  // 直接呼叫 Worker 入口，不連線 Discord。
  async function send(interaction: unknown) {
    return worker.fetch(
      await discord.signedRequest(JSON.stringify(interaction)),
      discord.bindings,
    );
  }

  // 頻道不同不影響授權；type 4 是文字回覆，flags 64 是僅操作者可見。
  it.each(['567890123456789012', '678901234567890123'])(
    'replies privately to the owner in channel %s of the allowed guild',
    async (channel_id) => {
      const response = await send(command({ channel_id }));

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      expect(await response.json()).toEqual({
        type: 4,
        data: { content: 'Pong!', flags: 64 },
      });
    },
  );

  // 管理員權限、假冒參數或不完整身分都不能繞過帳號與伺服器核對。
  it.each([
    ['another user', { member: { user: { id: '789012345678901234' } } }],
    ['another user with administrator permission', {
      member: { user: { id: '789012345678901234' }, permissions: '8' },
    }],
    ['another guild', { guild_id: '890123456789012345' }],
    ['a DM from the owner', {
      guild_id: undefined,
      member: undefined,
      user: { id: '234567890123456789' },
    }],
    ['missing guild', { guild_id: undefined }],
    ['numeric guild ID', { guild_id: 345678901234567890 }],
    ['missing member', { member: undefined }],
    ['null member', { member: null }],
    ['an array instead of a member', { member: [] }],
    ['missing member user', { member: {} }],
    ['null member user', { member: { user: null } }],
    ['missing user ID', { member: { user: {} } }],
    ['numeric user ID', { member: { user: { id: 234567890123456789 } } }],
    ['an owner ID supplied through command input', {
      member: { user: { id: '789012345678901234' } },
      data: {
        name: 'ping', type: 1,
        options: [{ name: 'owner', type: 3, value: '234567890123456789' }],
      },
    }],
    ['an owner identity supplied outside the guild member', {
      member: { user: { id: '789012345678901234', username: 'owner' }, roles: ['owner'] },
      user: { id: '234567890123456789' },
    }],
    ['an unknown command from another user', {
      member: { user: { id: '789012345678901234' } },
      data: { name: 'unknown', type: 1 },
    }],
  ])('privately denies %s without disclosing allowed IDs', async (_label, overrides) => {
    const response = await send(command(overrides));

    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toEqual({ type: 4, data: { content: '無法使用此指令', flags: 64 } });
    expect(JSON.stringify(body)).not.toContain(discord.bindings.DISCORD_OWNER_ID);
    expect(JSON.stringify(body)).not.toContain(discord.bindings.DISCORD_GUILD_ID);
  });

  // 已授權才回覆不支援；未授權的未知指令仍應收到拒絕提示。
  it('privately reports an unknown command after authorizing the owner', async () => {
    const response = await send(command({ data: { name: 'unknown', type: 1 } }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      type: 4,
      data: { content: '不支援此指令', flags: 64 },
    });
  });

  it.each([2, 3])('does not run a context-menu command named ping (type %s)', async (type) => {
    const response = await send(command({ data: { name: 'ping', type } }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      type: 4,
      data: { content: '不支援此指令', flags: 64 },
    });
  });

  // 無法辨識的指令資料屬格式錯誤，與授權拒絕分開處理。
  it.each([
    ['missing data', undefined],
    ['null data', null],
    ['an array', []],
    ['a string', 'ping'],
    ['missing name', { type: 1 }],
    ['an empty name', { name: '', type: 1 }],
    ['a blank name', { name: ' ', type: 1 }],
    ['a numeric name', { name: 1, type: 1 }],
    ['missing command type', { name: 'ping' }],
    ['a text command type', { name: 'ping', type: '1' }],
    ['a fractional command type', { name: 'ping', type: 1.5 }],
    ['an invalid command type', { name: 'ping', type: 0 }],
  ])('returns 400 for signed malformed command data: %s', async (_label, data) => {
    const response = await send(command({ data }));

    expect(response.status).toBe(400);
    expect(await response.text()).toBe('Invalid interaction');
  });

  it('rejects a signed command for another application before checking the owner', async () => {
    const response = await send(command({ application_id: '890123456789012345' }));

    expect(response.status).toBe(400);
  });

  it('does not authorize an owner claim in a forged request', async () => {
    const request = await discord.signedRequest(JSON.stringify(command()));
    request.headers.set('x-signature-ed25519', '00'.repeat(64));

    expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
  });

  // 攔截對外 HTTP 與日誌，確認回覆直接完成且不洩漏私人輸入。
  it.each([
    ['success', {}, 'Pong!'],
    ['denial', { member: { user: { id: '789012345678901234' } } }, '無法使用此指令'],
    ['unsupported command', { data: { name: 'unknown', type: 1 } }, '不支援此指令'],
  ])('replies directly for %s without external requests or logging private input', async (
    _label, overrides, content,
  ) => {
    const externalFetch = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Unexpected external request'));
    const errorLog = vi.spyOn(console, 'error').mockImplementation(() => {});
    const infoLog = vi.spyOn(console, 'log').mockImplementation(() => {});
    const privateInput = 'private-command-body-and-token';

    try {
      const response = await send(command({ ...overrides, token: privateInput }));

      expect(response.status).toBe(200);
      expect(await response.json()).toEqual({ type: 4, data: { content, flags: 64 } });
      expect(externalFetch).not.toHaveBeenCalled();
      expect([...errorLog.mock.calls, ...infoLog.mock.calls].flat().map(String).join(' '))
        .not.toContain(privateInput);
    } finally {
      externalFetch.mockRestore();
      errorLog.mockRestore();
      infoLog.mockRestore();
    }
  });
});
