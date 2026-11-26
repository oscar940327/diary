import { applyD1Migrations, reset } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { afterEach, expect, it, vi } from 'vitest';
import { formatEntryMessages, sendEntryMessage, verifyDiaryChannel } from '../src/entry-display';
import { saveEntry } from '../src/entry-storage';
import { publishEntry } from '../src/publish-entry';

const target = { guildId: '123', channelId: '456', botToken: 'fake-bot-token' };

afterEach(() => vi.restoreAllMocks());

it.each(['短文', 'a'.repeat(1981) + '😀\n' + '日'.repeat(2016)])('分段保留原文並將標示計入單則上限', (original) => {
  const parts = formatEntryMessages('2026-11-25', original);
  expect(parts.map(part => part.slice(part.indexOf('\n') + 1)).join('')).toBe(original);
  for (const [index, part] of parts.entries()) {
    expect(part.startsWith(`2026-11-25（${index + 1}/${parts.length}）\n`)).toBe(true);
    expect(part.length).toBeLessThanOrEqual(2_000);
    expect(part).not.toMatch(/[\uD800-\uDBFF]$|\n[\uDC00-\uDFFF]/u);
  }
});

it('只向核對過的指定頻道發送並抑制通知和預覽', async () => {
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(Response.json({ id: '456', guild_id: '123', type: 0 }))
    .mockResolvedValueOnce(Response.json({ id: '789', channel_id: '456' }));
  const verified = await verifyDiaryChannel(target, AbortSignal.timeout(1_000));
  expect(verified).toMatchObject({ ok: true });
  if (!verified.ok) throw new Error('未核對頻道');
  expect(await sendEntryMessage(verified.channel, '@everyone <@123> https://example.com', 'stable', AbortSignal.timeout(1_000)))
    .toEqual({ ok: true, messageId: '789' });
  expect(outbound.mock.calls.map(call => call[0])).toEqual([
    'https://discord.com/api/v10/channels/456',
    'https://discord.com/api/v10/channels/456/messages',
  ]);
  const request = outbound.mock.calls[1]?.[1];
  expect(new Headers(request?.headers).get('authorization')).toBe('Bot fake-bot-token');
  expect(JSON.parse(String(request?.body))).toEqual({
    content: '@everyone <@123> https://example.com', allowed_mentions: { parse: [] },
    flags: 4, nonce: 'stable', enforce_nonce: true,
  });
});

it.each([{ id: '999', guild_id: '123', type: 0 }, { id: '456', guild_id: '999', type: 0 }, { id: '456', guild_id: '123', type: 11 }])(
  '拒絕與設定不符或不支援的頻道', async (channel) => {
    const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(Response.json(channel));
    expect(await verifyDiaryChannel(target, AbortSignal.timeout(1_000))).toEqual({ ok: false, reason: 'channel' });
    expect(outbound).toHaveBeenCalledTimes(1);
  },
);

async function makeEntry() {
  await reset();
  await applyD1Migrations(env.DB, env.TEST_D1_MIGRATIONS);
  const result = await saveEntry(env.DB, {
    applicationId: '111', ownerId: '222', guildId: '123', submissionId: '333',
    originalContent: '日'.repeat(2_100), requestedDate: null, entryDate: '2026-11-25', createdAt: '2026-11-25T12:00:00Z',
  });
  if (result.status !== 'saved') throw new Error('未建立測試紀錄');
  return result.entry;
}

const channelResponse = () => Response.json({ id: '456', guild_id: '123', type: 0 });
const sentResponse = (id: string) => Response.json({ id, channel_id: '456' });

it('部分送達後只補送未確認片段，並沿用原本的 nonce', async () => {
  const entry = await makeEntry();
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(channelResponse())
    .mockResolvedValueOnce(sentResponse('789'))
    .mockRejectedValueOnce(new TypeError('Network connection lost.'))
    .mockResolvedValueOnce(channelResponse())
    .mockResolvedValueOnce(sentResponse('790'));
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000)))
    .toEqual({ status: 'failed', reason: 'uncertain', uncertain: true });
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'sent' });
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'sent' });
  const posts = outbound.mock.calls.filter(([, request]) => request?.method === 'POST');
  expect(posts).toHaveLength(3);
  expect(posts[2]?.[1]?.body).toBe(posts[1]?.[1]?.body);
  const rows = await env.DB.prepare('SELECT status, message_id FROM entry_messages WHERE entry_id = ? ORDER BY position')
    .bind(entry.id).all();
  expect(rows.results).toEqual([{ status: 'sent', message_id: '789' }, { status: 'sent', message_id: '790' }]);
});

it('有效鎖阻止同時發送，逾期工作可由另一個流程接手', async () => {
  const entry = await makeEntry();
  await env.DB.prepare('UPDATE entries SET display_lock_id = ?, display_lock_expires_at_ms = ? WHERE id = ?')
    .bind('interrupted', Date.now() + 35_000, entry.id).run();
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(channelResponse())
    .mockResolvedValueOnce(sentResponse('789'))
    .mockResolvedValueOnce(sentResponse('790'));
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'busy' });
  expect(outbound).not.toHaveBeenCalled();
  await env.DB.prepare('UPDATE entries SET display_lock_expires_at_ms = 0 WHERE id = ?').bind(entry.id).run();
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'sent' });
  expect(outbound).toHaveBeenCalledTimes(3);
});

it('發送成功但進度寫入中斷時，保留可能已送達及相同 nonce', async () => {
  const entry = await makeEntry();
  const db = {
    prepare(sql: string) {
      if (sql.includes('SET status = ?, channel_id = ?, message_id = ?')) throw new Error('模擬進度中斷');
      return env.DB.prepare(sql);
    },
    batch: env.DB.batch.bind(env.DB),
  } as D1Database;
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(channelResponse())
    .mockResolvedValueOnce(sentResponse('789'))
    .mockResolvedValueOnce(channelResponse())
    .mockResolvedValueOnce(sentResponse('789'))
    .mockResolvedValueOnce(sentResponse('790'));
  expect(await publishEntry(db, entry, target, AbortSignal.timeout(2_000)))
    .toEqual({ status: 'failed', reason: 'uncertain', uncertain: true });
  expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'sent' });
  expect(outbound.mock.calls[1]?.[1]?.body).toBe(outbound.mock.calls[3]?.[1]?.body);
});

it('並行發送時只有取得鎖的操作接觸 Discord', async () => {
  const entry = await makeEntry();
  const channelStarted = Promise.withResolvers<void>();
  const release = Promise.withResolvers<Response>();
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockImplementationOnce(() => { channelStarted.resolve(); return release.promise; })
    .mockResolvedValueOnce(sentResponse('789'))
    .mockResolvedValueOnce(sentResponse('790'));
  const first = publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000));
  await channelStarted.promise;
  try {
    expect(await publishEntry(env.DB, entry, target, AbortSignal.timeout(2_000))).toEqual({ status: 'busy' });
    expect(outbound).toHaveBeenCalledTimes(1);
  } finally {
    release.resolve(channelResponse());
    expect(await first).toEqual({ status: 'sent' });
  }
});
