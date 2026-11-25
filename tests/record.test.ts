import { applyD1Migrations, createExecutionContext, reset, waitOnExecutionContext } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { afterEach, beforeAll, expect, it, vi } from 'vitest';
import worker from '../src/index';
import { findEntryBySubmission } from '../src/entry-storage';
import { validateRecordInput } from '../src/record-input';
import { createDiscordFixture } from './helpers/discord';

const submissionId = '456789012345678901';
const beforeTaipeiMidnightId = '1575179251613696001'; // 2026-11-25 23:59:59 台北
const atTaipeiMidnightId = '1575179255808000001'; // 2026-11-26 00:00:00 台北
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
    id: atTaipeiMidnightId,
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

function mockDiscordReplies() {
  const acknowledge = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }));
  const update = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }));
  vi.spyOn(globalThis, 'fetch').mockImplementation((url, request) => {
    if (request?.method === 'POST') return acknowledge(url, request);
    if (request?.method === 'PATCH') return update(url, request);
    throw new Error('Unexpected outbound request');
  });
  return { acknowledge, update };
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

it('never starts a D1 write when Discord rejects the private acknowledgment', async () => {
  const readDatabase = vi.fn(() => { throw new Error('Unexpected D1 access'); });
  const outbound = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 404 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});

  const { response, settled } = await send(formSubmission(), { DB: { prepare: readDatabase } });
  await settled();

  expect(readDatabase).not.toHaveBeenCalled();
  expect(response.status).toBe(202);
  expect(outbound).toHaveBeenCalledExactlyOnceWith(
    `https://discord.com/api/v10/interactions/${atTaipeiMidnightId}/test-interaction-token/callback`,
    expect.objectContaining({ method: 'POST' }),
  );
  expect(errors.mock.calls).toEqual([['RECORD_ACKNOWLEDGMENT_FAILED']]);
});

it('never starts a D1 write when the Discord acknowledgment times out', async () => {
  const readDatabase = vi.fn(() => { throw new Error('Unexpected D1 access'); });
  const { acknowledge, update } = mockDiscordReplies();
  acknowledge.mockImplementation(async (_url, request) => {
    const signal = request?.signal;
    if (!signal) throw new Error('Missing acknowledgment deadline');
    await scheduler.wait(3_000, { signal });
    return new Response(null, { status: 204 });
  });
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});

  const { response, settled } = await send(formSubmission(), { DB: { prepare: readDatabase } });
  await settled();

  expect(response.status).toBe(202);
  expect(acknowledge).toHaveBeenCalledTimes(1);
  expect(acknowledge.mock.lastCall?.[1]?.signal?.aborted).toBe(true);
  expect(readDatabase).not.toHaveBeenCalled();
  expect(update).not.toHaveBeenCalled();
  expect(errors.mock.calls).toEqual([['RECORD_ACKNOWLEDGMENT_FAILED']]);
});

it('acknowledges the submission before the D1 write and updates the same private reply after saving', async () => {
  await freshDatabase();
  const { acknowledge, update } = mockDiscordReplies();
  const acknowledgment = Promise.withResolvers<Response>();
  acknowledge.mockReturnValue(acknowledgment.promise);
  const writeGate = Promise.withResolvers<void>();
  const prepare = vi.fn((sql: string) => ({
    bind(...values: unknown[]) {
      return {
        async first() {
          await writeGate.promise;
          return env.DB.prepare(sql).bind(...values).first();
        },
      };
    },
  }));
  const originalContent = '  保留原文 🐈\r\n第二行\n';
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-11-25T16:00:00.000Z'));

  const { response, settled } = await send(formSubmission(originalContent), { DB: { prepare } });
  try {
    expect(response.status).toBe(202);
    expect(await response.text()).toBe('');
    expect(acknowledge).toHaveBeenCalledExactlyOnceWith(
      `https://discord.com/api/v10/interactions/${atTaipeiMidnightId}/test-interaction-token/callback`,
      expect.objectContaining({ method: 'POST' }),
    );
    expect(JSON.parse(String(acknowledge.mock.lastCall?.[1]?.body))).toEqual({ type: 5, data: { flags: 64 } });
    expect(prepare).not.toHaveBeenCalled();
    expect(update).not.toHaveBeenCalled();
  } finally {
    acknowledgment.resolve(new Response(null, { status: 204 }));
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
  expect(prepare).toHaveBeenCalledTimes(1);
  expect(update).toHaveBeenCalledExactlyOnceWith(
    'https://discord.com/api/v10/webhooks/123456789012345678/test-interaction-token/messages/@original',
    expect.objectContaining({ method: 'PATCH' }),
  );
  expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toMatchObject({ content: '日記已保存。' });
});

it('privately reports an unconfirmed save before a slow D1 write finishes', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  const writeGate = Promise.withResolvers<void>();
  const write = Promise.withResolvers<unknown>();
  const db = {
    prepare(sql: string) {
      return {
        bind(...values: unknown[]) {
          return {
            first() {
              write.resolve(writeGate.promise.then(() => env.DB.prepare(sql).bind(...values).first()));
              return write.promise;
            },
          };
        },
      };
    },
  };
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });

  const { response, settled } = await send(formSubmission(), { DB: db });
  try {
    expect(response.status).toBe(202);
    await vi.advanceTimersByTimeAsync(20_000);
    expect(update).toHaveBeenCalledTimes(1);
    expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toHaveProperty(
      'content',
      expect.stringContaining('保存結果未確認'),
    );
  } finally {
    writeGate.resolve();
    await settled();
    vi.useRealTimers();
  }

  await write.promise;
  expect(await savedEntry()).toMatchObject({ originalContent: '今天的日記' });
  expect(update).toHaveBeenCalledTimes(1);
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

it('privately explains how to configure D1 instead of opening a form when the binding is missing', async () => {
  const { response } = await send(recordCommand());

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({
    type: 4,
    data: { flags: 64, content: '日記功能尚未設定資料庫，請完成設定後再執行 /record。' },
  });
});

it('privately explains how to proceed if the D1 binding is missing at submission', async () => {
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
  const { update } = mockDiscordReplies();
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(response.status).toBe(202);
  await settled();
  expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toHaveProperty(
    'content',
    '日記未保存，資料庫尚未初始化，請套用資料表遷移後重新送出。',
  );
});

it.each([
  ["Your account has exceeded D1's free tier daily row write limit.", '每日額度已用完', '等額度重置'],
  ["Your account has exceeded D1's free tier daily row read limit.", '每日額度已用完', '等額度重置'],
  ["Your account has exceeded D1's maximum account storage limit.", '儲存空間已達上限', '釋出空間'],
  ['Exceeded maximum DB size.', '儲存空間已達上限', '釋出空間'],
])('reports a confirmed refusal when D1 rejects the insert with %s', async (reason, explanation, nextStep) => {
  const db = {
    prepare() {
      return {
        bind: () => ({ first: async () => { throw new Error(`D1_ERROR: ${reason}`); } }),
      };
    },
  };
  const { update } = mockDiscordReplies();
  const { response, settled } = await send(formSubmission(), { DB: db });

  expect(response.status).toBe(202);
  await settled();
  const { content } = JSON.parse(String(update.mock.lastCall?.[1]?.body));
  expect(content).toContain('日記未保存');
  expect(content).toContain(explanation);
  expect(content).toContain(nextStep);
});

it('reports uncertainty when the quota prevents checking an existing submission', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  const first = await send(formSubmission(), { DB: env.DB });
  await first.settled();
  const original = await savedEntry();
  expect(original).not.toBeNull();

  const prepare = vi.fn()
    .mockImplementationOnce((sql: string) => env.DB.prepare(sql))
    .mockImplementationOnce(() => {
      throw new Error("D1_ERROR: Your account has exceeded D1's free tier daily row read limit.");
    });
  const retry = await send({
    ...formSubmission(), id: beforeTaipeiMidnightId, token: 'replay-interaction-token',
  }, { DB: { prepare } });
  await retry.settled();

  expect(prepare).toHaveBeenCalledTimes(2);
  expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toHaveProperty(
    'content', expect.stringContaining('保存結果未確認'),
  );
  expect(await savedEntry()).toEqual(original);
});

it('reports an unknown write outcome without saying the entry was saved or leaking details', async () => {
  const original = '私人內容代碼';
  const db = { prepare() { throw new Error(`Network connection lost: ${original}`); } };
  const { update } = mockDiscordReplies();
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(original), { DB: db });

  expect(response.status).toBe(202);
  await settled();
  const reply = String(update.mock.lastCall?.[1]?.body);
  expect(JSON.parse(reply)).toHaveProperty('content', expect.stringContaining('保存結果未確認'));
  expect(reply).not.toContain(original);
  expect(reply).not.toContain('Network connection lost');
  expect(reply).not.toContain('test-interaction-token');
  expect(errors.mock.calls).toEqual([]);
});

it('reports a conflicting submission without replacing the saved content', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  const first = await send(formSubmission('原文', '2024-02-29'), { DB: env.DB });
  await first.settled();
  const original = await savedEntry();
  expect(original).toMatchObject({ originalContent: '原文', entryDate: '2024-02-29' });

  const changed = await send(
    { ...formSubmission('修改內容', '2024-02-29'), id: beforeTaipeiMidnightId, token: 'replay-interaction-token' },
    { DB: env.DB },
  );
  expect(changed.response.status).toBe(202);
  await changed.settled();
  expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toHaveProperty('content', expect.stringContaining('重新開啟表單'));
  expect(await savedEntry()).toEqual(original);
});

it('keeps the saved entry when Discord rejects the private update and logs only a reason code', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  update.mockResolvedValue(new Response('秘密錯誤本文', { status: 500 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(response.status).toBe(202);
  await settled();
  expect(await savedEntry()).toMatchObject({ originalContent: '今天的日記' });
  expect(update).toHaveBeenCalledTimes(1);
  expect(errors.mock.calls).toEqual([['RECORD_REPLY_UPDATE_FAILED']]);
});

it('keeps the saved entry without retrying a private reply Discord reports as missing', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  update.mockResolvedValueOnce(new Response(null, { status: 404 }));
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(response.status).toBe(202);
  await settled();
  expect(update).toHaveBeenCalledTimes(1);
  expect(errors.mock.calls).toEqual([['RECORD_REPLY_UPDATE_FAILED']]);
  expect(await savedEntry()).toMatchObject({ originalContent: '今天的日記' });
});

it('keeps the saved entry when updating the private reply times out', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  update.mockImplementation(async (_url, request) => {
    const signal = request?.signal;
    if (!signal) throw new Error('Missing reply deadline');
    await scheduler.wait(5_000, { signal });
    return new Response(null, { status: 204 });
  });
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  const { response, settled } = await send(formSubmission(), { DB: env.DB });

  expect(response.status).toBe(202);
  await settled();
  expect(update).toHaveBeenCalledTimes(1);
  expect(update.mock.lastCall?.[1]?.signal?.aborted).toBe(true);
  expect(errors.mock.calls).toEqual([['RECORD_REPLY_UPDATE_FAILED']]);
  expect(await savedEntry()).toMatchObject({ originalContent: '今天的日記' });
}, 10_000);

it('uses the submission day when an undated form reaches the Worker after Taipei midnight', async () => {
  await freshDatabase();
  mockDiscordReplies();
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-11-25T16:00:05.000Z'));

  const { response, settled } = await send({ ...formSubmission(), id: beforeTaipeiMidnightId }, { DB: env.DB });
  expect(response.status).toBe(202);
  await settled();
  expect(await savedEntry()).toMatchObject({
    entryDate: '2026-11-25',
    requestedDate: null,
    createdAt: '2026-11-25T16:00:05.000Z',
  });
});

it('rejects a date still in the future at submission even if the Worker receives it after Taipei midnight', async () => {
  const { bindings, readDatabase, outbound } = unusedResources();
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-11-25T16:00:05.000Z'));

  const { response, settled } = await send(
    { ...formSubmission('今天的日記', '2026-11-26'), id: beforeTaipeiMidnightId },
    bindings,
  );
  expect(await response.json()).toMatchObject({
    type: 4,
    data: { flags: 64, content: expect.stringContaining('今天或過去的日期') },
  });
  await settled();
  expect(readDatabase).not.toHaveBeenCalled();
  expect(outbound).not.toHaveBeenCalled();
});

it.each([undefined, 'invalid', '18446744073709551616'])(
  'rejects a submission ID of %s before saving',
  async (id) => {
    const { bindings, readDatabase, outbound } = unusedResources();
    const { response, settled } = await send({ ...formSubmission(), id }, bindings);

    expect(response.status).toBe(400);
    await settled();
    expect(readDatabase).not.toHaveBeenCalled();
    expect(outbound).not.toHaveBeenCalled();
  },
);

it('keeps distinct entries on the same day and preserves the original date when a form is replayed', async () => {
  await freshDatabase();
  const { update } = mockDiscordReplies();
  const secondId = '456789012345678902';
  const secondInteractionId = '1575179251613696002';
  vi.useFakeTimers({ toFake: ['Date'] });
  try {
    vi.setSystemTime(new Date('2026-11-25T15:59:59.000Z'));
    for (const [formId, interactionId] of [[submissionId, beforeTaipeiMidnightId], [secondId, secondInteractionId]] as const) {
      const payload = { ...formSubmission('相同文字', '', formId), id: interactionId };
      const { response, settled } = await send(payload, { DB: env.DB });
      expect(response.status).toBe(202);
      await settled();
    }
    const original = await savedEntry();
    expect(original).toMatchObject({ entryDate: '2026-11-25', createdAt: '2026-11-25T15:59:59.000Z' });
    const second = await savedEntry(secondId);
    expect(second).toMatchObject({ entryDate: '2026-11-25', originalContent: '相同文字' });
    expect(second?.id).not.toBe(original?.id);

    vi.setSystemTime(new Date('2026-11-25T16:00:00.000Z'));
    const replayId = atTaipeiMidnightId;
    const replay = await send(
      { ...formSubmission('相同文字'), id: replayId, token: 'replay-interaction-token' },
      { DB: env.DB },
    );
    expect(replay.response.status).toBe(202);
    await replay.settled();
    expect(await savedEntry()).toEqual(original);
    expect(await savedEntry(replayId)).toBeNull();
    expect(update.mock.lastCall?.[0]).toContain('/replay-interaction-token/messages/@original');
    expect(JSON.parse(String(update.mock.lastCall?.[1]?.body))).toHaveProperty('content', '日記已保存。');
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
  const { response } = await send(recordCommand(), { DB: env.DB });
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
