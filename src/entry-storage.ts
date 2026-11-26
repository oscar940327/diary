export type EntryScope = {
  applicationId: string;
  ownerId: string;
  guildId: string;
};
type SubmissionKey = EntryScope & { submissionId: string };

export type EntrySubmission = SubmissionKey & {
  originalContent: string;
  // 表單的選填日期與算出的歸屬日期分開，讓跨日重送能辨識同一份輸入。
  requestedDate: string | null;
  entryDate: string;
  createdAt: string;
};

export type Entry = EntrySubmission & {
  id: string;
  displayStatus: 'pending' | 'sent' | 'uncertain';
};

type SaveEntryResult =
  | { status: 'saved' | 'duplicate'; entry: Entry }
  | { status: 'conflict' };

export class EntryInsertError extends Error {
  readonly quota: 'daily' | 'storage' | null;

  constructor(cause: Error) {
    super(cause.message, { cause });
    this.quota = insertQuota(cause.message);
  }
}

function insertQuota(message: string): EntryInsertError['quota'] {
  if (/^D1_ERROR: Your account has exceeded D1's free tier daily row (?:read|write) limit(?:\.|$)/.test(message)) {
    return 'daily';
  }
  if (
    /^D1_ERROR: Your account has exceeded D1's maximum account storage limit(?:[,\.]|$)/.test(message)
    || /^D1_ERROR: Exceeded maximum DB size(?:\.|$)/.test(message)
  ) {
    return 'storage';
  }
  return null;
}

export function isDailyQuotaError(error: unknown): boolean {
  return error instanceof Error && insertQuota(error.message) === 'daily';
}

const entryColumns = `
  id,
  application_id AS applicationId,
  owner_id AS ownerId,
  guild_id AS guildId,
  submission_id AS submissionId,
  original_content AS originalContent,
  requested_date AS requestedDate,
  entry_date AS entryDate,
  created_at AS createdAt,
  display_status AS displayStatus
`;

// 呼叫端先完成身分、內容及日期驗證，再交給這裡保存。
// 資料庫錯誤往上傳遞，只有取得資料列才能回報已保存。
export async function saveEntry(db: D1Database, submission: EntrySubmission): Promise<SaveEntryResult> {
  let entry: Entry | null;
  let quotaRejection: EntryInsertError | undefined;
  try {
    entry = await db.prepare(`
      INSERT INTO entries (
        id, application_id, owner_id, guild_id, submission_id, original_content,
        requested_date, entry_date, created_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT (application_id, owner_id, guild_id, submission_id) DO NOTHING
      RETURNING ${entryColumns}
    `).bind(
      crypto.randomUUID(),
      submission.applicationId,
      submission.ownerId,
      submission.guildId,
      submission.submissionId,
      submission.originalContent,
      submission.requestedDate,
      submission.entryDate,
      submission.createdAt,
    ).first<Entry>();
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    const failure = new EntryInsertError(error);
    if (failure.quota === null) throw failure;
    quotaRejection = failure;
    entry = null;
  }

  if (entry !== null) {
    return { status: 'saved', entry };
  }

  // 新增發生衝突或被額度拒絕時，這份提交仍可能已存在。
  const existing = await findEntryBySubmission(db, submission);
  if (existing === null) {
    throw quotaRejection ?? new Error('Existing entry could not be confirmed');
  }
  // 未填日期的重送沿用首次保存的日期及時間，即使重送時已跨日。
  if (
    existing.originalContent !== submission.originalContent
    || existing.requestedDate !== submission.requestedDate
  ) {
    return { status: 'conflict' };
  }
  return { status: 'duplicate', entry: existing };
}

export async function findEntryBySubmission(db: D1Database, key: SubmissionKey): Promise<Entry | null> {
  return db.prepare(`
    SELECT ${entryColumns}
    FROM entries
    WHERE application_id = ? AND owner_id = ? AND guild_id = ? AND submission_id = ?
  `).bind(key.applicationId, key.ownerId, key.guildId, key.submissionId).first<Entry>();
}

export async function findEntryById(db: D1Database, scope: EntryScope, id: string): Promise<Entry | null> {
  return db.prepare(`
    SELECT ${entryColumns} FROM entries
    WHERE id = ? AND application_id = ? AND guild_id = ? AND owner_id = ?
  `).bind(id, scope.applicationId, scope.guildId, scope.ownerId).first<Entry>();
}
