import { applyD1Migrations, createExecutionContext, reset, waitOnExecutionContext } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { afterEach, beforeAll, expect, it, vi } from 'vitest';
import worker from '../src/index';
import { findEntryBySubmission } from '../src/entry-storage';
import { validateRecordInput } from '../src/record-input';
import { createDiscordFixture } from './helpers/discord';

const submissionId = '456789012345678901';
let discord: Awaited<ReturnType<typeof createDiscordFixture>>;

beforeAll(async () => {
  discord = await createDiscordFixture();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

function interaction(data: Record<string, unknown>) {
  return {
    application_id: discord.bindings.DISCORD_APPLICATION_ID,
    guild_id: discord.bindings.DISCORD_GUILD_ID,
    member: { user: { id: discord.bindings.DISCORD_OWNER_ID } },
    ...data,
  };
}

function recordCommand() {
  return interaction({ id: submissionId, type: 2, data: { name: 'record', type: 1 } });
}

function formSubmission(content = '今天的日記', date = '', id = submissionId) {
  return interaction({
    id: '567890123456789012',
    type: 5,
    token: 'test-interaction-token',
    data: {
      custom_id: `record:${id}`,
      components: [
        { type: 18, component: { type: 4, custom_id: 'content', value: content } },
        { type: 18, component: { type: 4, custom_id: 'date', value: date } },
      ],
    },
  });
}

function unusedResources() {
  const readDatabase = vi.fn(() => { throw new Error('Unexpected D1 access'); });
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  return { bindings: { DB: { prepare: readDatabase } }, readDatabase, outbound };
}

function savedEntry(id = submissionId) {
  return findEntryBySubmission(env.DB, {
    applicationId: discord.bindings.DISCORD_APPLICATION_ID,
    guildId: discord.bindings.DISCORD_GUILD_ID,
    ownerId: discord.bindings.DISCORD_OWNER_ID,
    submissionId: id,
  });
}

async function freshDatabase() {
  await reset();
  await applyD1Migrations(env.DB, env.TEST_D1_MIGRATIONS);
}

it('acknowledges the submission before the D1 write and updates the same private reply after saving', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const writeGate = Promise.withResolvers<void>();
  const db = {
    prepare(sql: string) {
      return {
        bind(...values: unknown[]) {
          return {
            async first() {
              await writeGate.promise;
              return env.DB.prepare(sql).bind(...values).first();
            },
          };
        },
      };
    },
  };
  const originalContent = '  保留原文 🐈\r\n第二行\n';
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-11-25T16:00:00.000Z'));

  const { response, settled } = await send(formSubmission(originalContent), { DB: db });
  try {
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
    expect(await savedEntry()).toBeNull();
    expect(outbound).not.toHaveBeenCalled();
  } finally {
    writeGate.resolve();
    await settled();
    vi.useRealTimers();
  }

  expect(await savedEntry()).toMatchObject({
    originalContent,
    entryDate: '2026-11-26',
    requestedDate: null,
    createdAt: '2026-11-25T16:00:00.000Z',
    displayStatus: 'pending',
  });
  expect(outbound).toHaveBeenCalledExactlyOnceWith(
    'https://discord.com/api/v10/webhooks/123456789012345678/test-interaction-token/messages/@original',
    expect.objectContaining({ method: 'PATCH' }),
  );
  expect(JSON.parse(String(outbound.mock.calls[0]?.[1]?.body))).toMatchObject({ content: '日記已保存。' });
});

it('leaves no entry when a form is opened and never submitted', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const { response, settled } = await send(recordCommand(), { DB: env.DB });

  expect(await response.json()).toHaveProperty('type', 9);
  await settled();
  expect(await savedEntry()).toBeNull();
  expect(outbound).not.toHaveBeenCalled();
});

it('privately explains how to proceed when the D1 binding is missing', async () => {
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const { response, settled } = await send(formSubmission());

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({
    type: 4,
    data: { flags: 64, content: '日記未保存，資料庫尚未設定，請完成設定後重新送出。' },
  });
  await settled();
  expect(outbound).not.toHaveBeenCalled();
});

it('reports a confirmed write failure when the local schema has not been applied', async () => {
  await reset();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
  await settled();
  expect(JSON.parse(String(outbound.mock.lastCall?.[1]?.body))).toHaveProperty(
    'content',
    '日記未保存，資料庫尚未初始化，請套用資料表遷移後重新送出。',
  );
});

it('reports an unknown write outcome without saying the entry was saved or leaking details', async () => {
  const original = '私人內容代碼';
  const db = { prepare() { throw new Error(`Network connection lost: ${original}`); } };
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(original), { DB: db });

  expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
  await settled();
  const reply = String(outbound.mock.lastCall?.[1]?.body);
  expect(JSON.parse(reply)).toHaveProperty('content', expect.stringContaining('保存結果未確認'));
  expect(reply).not.toContain(original);
  expect(reply).not.toContain('Network connection lost');
  expect(reply).not.toContain('test-interaction-token');
  expect(errors.mock.calls).toEqual([]);
});

it('reports a conflicting submission without replacing the saved content', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const first = await send(formSubmission('原文', '2024-02-29'), { DB: env.DB });
  await first.settled();
  const original = await savedEntry();
  expect(original).toMatchObject({ originalContent: '原文', entryDate: '2024-02-29' });

  const changed = await send(formSubmission('修改內容', '2024-02-29'), { DB: env.DB });
  expect(await changed.response.json()).toEqual({ type: 5, data: { flags: 64 } });
  await changed.settled();
  expect(JSON.parse(String(outbound.mock.lastCall?.[1]?.body))).toHaveProperty('content', expect.stringContaining('重新開啟表單'));
  expect(await savedEntry()).toEqual(original);
});

it('keeps the saved entry when Discord rejects the private update and logs only a reason code', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('秘密錯誤本文', { status: 500 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
  await settled();
  expect(await savedEntry()).toMatchObject({ originalContent: '今天的日記' });
  expect(outbound).toHaveBeenCalledTimes(1);
  expect(errors.mock.calls).toEqual([['RECORD_REPLY_UPDATE_FAILED']]);
});

it('retries the same private update once if the initial reply is not available yet', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(null, { status: 404 }))
    .mockResolvedValueOnce(new Response(null, { status: 204 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
  await settled();
  expect(outbound).toHaveBeenCalledTimes(2);
  expect(outbound.mock.calls[1]?.[0]).toBe(outbound.mock.calls[0]?.[0]);
  expect(outbound.mock.calls[1]?.[1]?.body).toBe(outbound.mock.calls[0]?.[1]?.body);
  expect(errors).not.toHaveBeenCalled();
});

it('keeps distinct entries on the same day and preserves the original date when a form is replayed', async () => {
  await freshDatabase();
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));
  const secondId = '456789012345678902';
  vi.useFakeTimers({ toFake: ['Date'] });
  try {
    vi.setSystemTime(new Date('2026-11-25T15:59:59.000Z'));
    for (const id of [submissionId, secondId]) {
      const { response, settled } = await send(formSubmission('相同文字', '', id), { DB: env.DB });
      expect(await response.json()).toEqual({ type: 5, data: { flags: 64 } });
      await settled();
    }
    const original = await savedEntry();
    expect(original).toMatchObject({ entryDate: '2026-11-25', createdAt: '2026-11-25T15:59:59.000Z' });
    const second = await savedEntry(secondId);
    expect(second).toMatchObject({ entryDate: '2026-11-25', originalContent: '相同文字' });
    expect(second?.id).not.toBe(original?.id);

    vi.setSystemTime(new Date('2026-11-25T16:00:00.000Z'));
    const replayId = '567890123456789013';
    const replay = await send(
      { ...formSubmission('相同文字'), id: replayId, token: 'replay-interaction-token' },
      { DB: env.DB },
    );
    expect(await replay.response.json()).toEqual({ type: 5, data: { flags: 64 } });
    await replay.settled();
    expect(await savedEntry()).toEqual(original);
    expect(await savedEntry(replayId)).toBeNull();
    expect(outbound.mock.lastCall?.[0]).toContain('/replay-interaction-token/messages/@original');
    expect(JSON.parse(String(outbound.mock.lastCall?.[1]?.body))).toHaveProperty('content', '日記已保存。');
  } finally {
    vi.useRealTimers();
  }
});

it.each([
  ['the default Taipei day', '   ', null, '2026-11-26'],
  ['an explicitly selected Taipei day', '2026-11-26', '2026-11-26', '2026-11-26'],
  ['a past leap day', ' 2024-02-29 ', '2024-02-29', '2024-02-29'],
] as const)('accepts %s and keeps all 4,000 units of input', (_label, rawDate, requestedDate, entryDate) => {
  const originalContent = ' \r\n' + '🐈'.repeat(1998) + ' ';
  expect(validateRecordInput(originalContent, rawDate, new Date('2026-11-25T16:00:00.000Z'))).toEqual({
    ok: true,
    originalContent,
    requestedDate,
    entryDate,
  });
});

async function send(payload: unknown, bindings: object = {}) {
  const ctx = createExecutionContext();
  const response = await worker.fetch(
    await discord.signedRequest(JSON.stringify(payload)),
    { ...discord.bindings, ...bindings },
    ctx,
  );
  return { response, settled: () => waitOnExecutionContext(ctx) };
}

it('opens a multiline diary form with an optional date for the owner', async () => {
  const { response } = await send(recordCommand());
  expect(response.status).toBe(200);
  expect(await response.json()).toMatchObject({
    type: 9,
    data: {
      custom_id: 'record:456789012345678901',
      components: [
        { type: 18, component: { type: 4, style: 2, custom_id: 'content', required: true, max_length: 4000 } },
        { type: 18, component: { type: 4, style: 1, custom_id: 'date', required: false } },
      ],
    },
  });
});

it.each([
  ['another user', { member: { user: { id: '789012345678901234' } } }],
  ['an administrator', { member: { user: { id: '789012345678901234' }, permissions: '8' } }],
  ['another guild', { guild_id: '890123456789012345' }],
  ['a DM', { guild_id: undefined, member: undefined, user: { id: '234567890123456789' } }],
  ['a missing member', { member: undefined }],
] as const)('privately rejects opening and submitting the form for %s', async (_label, overrides) => {
  const { bindings, readDatabase, outbound } = unusedResources();
  for (const payload of [recordCommand(), formSubmission()]) {
    const { response, settled } = await send({ ...payload, ...overrides }, bindings);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ type: 4, data: { flags: 64, content: '無法使用此指令' } });
    await settled();
  }
  expect(readDatabase).not.toHaveBeenCalled();
  expect(outbound).not.toHaveBeenCalled();
});

it.each([
  ['only whitespace', ' \t\n ', '', '請輸入內容'],
  ['more than 4,000 UTF-16 units', '🐈'.repeat(2000) + '字', '', '最多 4,000'],
  ['an ambiguous date', '日記', '11/24/2026', 'YYYY-MM-DD'],
  ['a nonexistent day', '日記', '2026-02-29', '有效日期'],
  ['a future Taipei date', '日記', '2026-11-27', '今天或過去'],
] as const)('privately rejects %s without saving', async (_label, content, date, reason) => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-11-25T16:00:00.000Z'));
  try {
    const { bindings, readDatabase, outbound } = unusedResources();
    const { response, settled } = await send(formSubmission(content, date), bindings);
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      type: 4,
      data: { flags: 64, content: expect.stringContaining(reason) },
    });
    await settled();
    expect(readDatabase).not.toHaveBeenCalled();
    expect(outbound).not.toHaveBeenCalled();
  } finally {
    vi.useRealTimers();
  }
});

it.each([
  ['an unknown form', { custom_id: 'other:456789012345678901', components: [] }],
  ['a missing content field', { custom_id: 'record:456789012345678901', components: [] }],
  ['a non-text component value', {
    custom_id: 'record:456789012345678901',
    components: [{ type: 18, component: { type: 4, custom_id: 'content', value: 123 } }],
  }],
  ['duplicate content fields', {
    custom_id: 'record:456789012345678901',
    components: [
      { type: 18, component: { type: 4, custom_id: 'content', value: '日記' } },
      { type: 18, component: { type: 4, custom_id: 'content', value: '重複' } },
    ],
  }],
] as const)('rejects %s before touching D1 or Discord', async (_label, data) => {
  const { bindings, readDatabase, outbound } = unusedResources();
  const { response, settled } = await send({ ...formSubmission(), data }, bindings);

  expect(response.status).toBe(400);
  expect(await response.text()).toBe('Invalid interaction');
  await settled();
  expect(readDatabase).not.toHaveBeenCalled();
  expect(outbound).not.toHaveBeenCalled();
});
