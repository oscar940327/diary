import { applyD1Migrations, reset, type D1Migration } from 'cloudflare:test';
import { env } from 'cloudflare:workers';
import { beforeEach, expect, it } from 'vitest';
import { findEntryBySubmission, saveEntry, type EntrySubmission } from '../src/entry-storage';

declare global {
  namespace Cloudflare {
    interface Env {
      DB: D1Database;
      TEST_D1_MIGRATIONS: D1Migration[];
    }
  }
}

// Workers 測試同檔共用儲存空間，每個案例重建自己的資料庫狀態。
beforeEach(async () => {
  await reset();
  await applyD1Migrations(env.DB, env.TEST_D1_MIGRATIONS);
});

const submission: EntrySubmission = {
  applicationId: '111111111111111111',
  ownerId: '222222222222222222',
  guildId: '333333333333333333',
  submissionId: '444444444444444444',
  originalContent: "  今天的日記 🐈\r\n\n保留 '引號' 和空白  ",
  requestedDate: '2026-11-23',
  entryDate: '2026-11-23',
  createdAt: '2026-11-25T09:30:00.000Z',
};

it('saves and retrieves the exact original content with a stable ID and pending display', async () => {
  const result = await saveEntry(env.DB, submission);

  expect(result).toMatchObject({
    status: 'saved',
    entry: { ...submission, id: expect.any(String), displayStatus: 'pending' },
  });
  expect(await findEntryBySubmission(env.DB, submission)).toEqual(
    result.status === 'saved' ? result.entry : undefined,
  );
});

it('propagates D1 failures when the database schema is unavailable', async () => {
  await reset();

  await expect(saveEntry(env.DB, submission)).rejects.toThrow(/no such table: entries/);
  await expect(findEntryBySubmission(env.DB, submission)).rejects.toThrow(/no such table: entries/);
});

it('creates one entry when the same submission arrives concurrently', async () => {
  const results = await Promise.all([
    saveEntry(env.DB, submission),
    saveEntry(env.DB, submission),
  ]);

  expect(results.map(result => result.status).sort()).toEqual(['duplicate', 'saved']);
  const entry = await findEntryBySubmission(env.DB, submission);
  expect(results[0]).toHaveProperty('entry', entry);
  expect(results[1]).toHaveProperty('entry', entry);
});

it.each([
  { originalContent: '改過的原文' },
  { requestedDate: '2026-11-24', entryDate: '2026-11-24' },
])('reports a conflict when a repeated submission changes its input', async (changes) => {
  const saved = await saveEntry(env.DB, submission);

  expect(await saveEntry(env.DB, { ...submission, ...changes })).toEqual({ status: 'conflict' });
  expect(saved).toHaveProperty('entry', await findEntryBySubmission(env.DB, submission));
});

it('keeps the original date and timestamp when a blank-date submission is replayed on another day', async () => {
  const first = { ...submission, requestedDate: null, entryDate: '2026-11-25' };
  const saved = await saveEntry(env.DB, first);
  const replay = await saveEntry(env.DB, {
    ...first,
    entryDate: '2026-11-26',
    createdAt: '2026-11-25T16:00:00.000Z',
  });

  expect(replay).toMatchObject({
    status: 'duplicate',
    entry: { requestedDate: null, entryDate: '2026-11-25', createdAt: '2026-11-25T09:30:00.000Z' },
  });
  expect(saved).toHaveProperty('entry', await findEntryBySubmission(env.DB, first));
});

it('preserves identical content as separate entries when the submission IDs differ', async () => {
  const second = { ...submission, submissionId: '555555555555555555' };

  await expect(saveEntry(env.DB, submission)).resolves.toHaveProperty('status', 'saved');
  await expect(saveEntry(env.DB, second)).resolves.toHaveProperty('status', 'saved');

  const firstEntry = await findEntryBySubmission(env.DB, submission);
  const secondEntry = await findEntryBySubmission(env.DB, second);
  expect(firstEntry?.id).not.toBe(secondEntry?.id);
});

it.each([
  { applicationId: '666666666666666666' },
  { guildId: '777777777777777777' },
  { ownerId: '888888888888888888' },
])('cannot retrieve an entry outside its submission scope', async (otherScope) => {
  await saveEntry(env.DB, submission);

  expect(await findEntryBySubmission(env.DB, { ...submission, ...otherScope })).toBeNull();
});
