type SubmissionKey = {
  applicationId: string;
  ownerId: string;
  guildId: string;
  submissionId: string;
};

export type EntrySubmission = SubmissionKey & {
  originalContent: string;
  // 表單的選填日期與算出的歸屬日期分開，讓跨日重送能辨識同一份輸入。
  requestedDate: string | null;
  entryDate: string;
  createdAt: string;
};

type Entry = EntrySubmission & {
  id: string;
  displayStatus: 'pending' | 'sent' | 'uncertain';
};

type SaveEntryResult =
  | { status: 'saved' | 'duplicate'; entry: Entry }
  | { status: 'conflict' };

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
  const entry = await db.prepare(`
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

  if (entry !== null) {
    return { status: 'saved', entry };
  }

  // 先由 D1 原子處理新增，再查詢已存在的同一筆提交。
  const existing = await findEntryBySubmission(db, submission);
  if (existing === null) {
    throw new Error('Existing entry could not be confirmed');
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
