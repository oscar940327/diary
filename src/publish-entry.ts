import type { Entry } from './entry-storage';
import { formatEntryMessages, sendEntryMessage, verifyDiaryChannel, type DiaryChannel, type DisplayFailure } from './entry-display';

export type DisplayResult =
  | { status: 'sent' }
  | { status: 'busy' }
  | { status: 'failed'; reason: DisplayFailure; uncertain?: boolean };
type Segment = { position: number; content: string; nonce: string; status: Entry['displayStatus']; channel_id: string | null };
const lockDurationMs = 35_000; // 長於單次 Worker 背景工作的上限。
const fence = 'SELECT 1 FROM entries WHERE id = ? AND display_lock_id = ? AND display_lock_expires_at_ms > ?';

export async function publishEntry(
  db: D1Database, entry: Entry, target: DiaryChannel, signal: AbortSignal,
): Promise<DisplayResult> {
  if (entry.guildId !== target.guildId) return { status: 'failed', reason: 'channel' };
  const lock = crypto.randomUUID();
  const start = Date.now();
  const acquired = await db.prepare(`
    UPDATE entries SET display_lock_id = ?, display_lock_expires_at_ms = ?
    WHERE id = ? AND display_status <> 'sent'
      AND (display_lock_id IS NULL OR display_lock_expires_at_ms <= ?)
  `).bind(lock, start + lockDurationMs, entry.id, start).run();
  if (acquired.meta.changes !== 1) {
    const status = await db.prepare('SELECT display_status FROM entries WHERE id = ?')
      .bind(entry.id).first<string>('display_status');
    return { status: status === 'sent' ? 'sent' : 'busy' };
  }

  let uncertain = entry.displayStatus === 'uncertain';
  try {
    signal.throwIfAborted();
    const parts = formatEntryMessages(entry.entryDate, entry.originalContent);
    const writes = await Promise.all(parts.map(async (content, index) => db.prepare(`
      INSERT INTO entry_messages (entry_id, position, content, nonce)
      SELECT ?, ?, ?, ? WHERE EXISTS (${fence})
      ON CONFLICT (entry_id, position) DO NOTHING
    `).bind(entry.id, index + 1, content, await segmentNonce(entry.id, index + 1), entry.id, lock, Date.now())));
    signal.throwIfAborted();
    await db.batch(writes);
    const { results: segments } = await db.prepare(`
      SELECT position, content, nonce, status, channel_id FROM entry_messages WHERE entry_id = ? ORDER BY position
    `).bind(entry.id).all<Segment>();
    if (segments.length === 0) return { status: 'failed', reason: 'unknown' };
    const pending = segments.filter(segment => segment.status !== 'sent');
    if (!pending.length) return { status: 'sent' };
    uncertain = pending.some(segment => segment.status === 'uncertain');
    if (segments.some(segment => segment.channel_id !== null && segment.channel_id !== target.channelId)) {
      return { status: 'failed', reason: 'channel', uncertain };
    }
    const channel = await verifyDiaryChannel(target, requestSignal(signal));
    if (!channel.ok) return { status: 'failed', reason: channel.reason, uncertain };

    for (const segment of pending) {
      signal.throwIfAborted();
      // 先留下「可能送達」，程序中斷後仍可用固定 nonce 恢復。
      const [marked] = await db.batch([
        db.prepare(`
          UPDATE entry_messages SET status = 'uncertain', channel_id = ?, failure_code = 'interrupted'
          WHERE entry_id = ? AND position = ? AND status <> 'sent' AND EXISTS (${fence})
        `).bind(target.channelId, entry.id, segment.position, entry.id, lock, Date.now()),
        db.prepare("UPDATE entries SET display_status = 'uncertain' WHERE EXISTS (" + fence + ') AND id = ?')
          .bind(entry.id, lock, Date.now(), entry.id),
      ]);
      if (marked?.meta.changes !== 1) return { status: 'busy' };
      uncertain = true;
      signal.throwIfAborted();
      const send = await sendEntryMessage(channel.channel, segment.content, segment.nonce, requestSignal(signal));
      const status = send.ok ? 'sent' : send.reason === 'uncertain' || segment.status === 'uncertain' ? 'uncertain' : 'pending';
      const updated = await db.prepare(`
        UPDATE entry_messages SET status = ?, channel_id = ?, message_id = ?, failure_code = ?
        WHERE entry_id = ? AND position = ? AND EXISTS (${fence})
      `).bind(
        status, status === 'pending' ? null : target.channelId, send.ok ? send.messageId : null,
        send.ok ? null : send.reason, entry.id, segment.position, entry.id, lock, Date.now(),
      ).run();
      if (updated.meta.changes !== 1) return { status: 'failed', reason: 'uncertain', uncertain: true };
      uncertain = pending.some(other => other.position > segment.position && other.status === 'uncertain')
        || status === 'uncertain';
      if (!send.ok) return { status: 'failed', reason: send.reason, uncertain };
    }
    return { status: 'sent' };
  } catch {
    return { status: 'failed', reason: uncertain ? 'uncertain' : signal.aborted ? 'timeout' : 'unknown', uncertain };
  } finally {
    // 舊工作即使晚到，也只能解除自己持有的鎖。
    await db.prepare(`
      UPDATE entries SET display_lock_id = NULL, display_lock_expires_at_ms = NULL,
        display_status = CASE
          WHEN EXISTS (SELECT 1 FROM entry_messages WHERE entry_id = entries.id AND status = 'uncertain') THEN 'uncertain'
          WHEN EXISTS (SELECT 1 FROM entry_messages WHERE entry_id = entries.id)
            AND NOT EXISTS (SELECT 1 FROM entry_messages WHERE entry_id = entries.id AND status <> 'sent') THEN 'sent'
          ELSE 'pending'
        END
      WHERE id = ? AND display_lock_id = ?
    `).bind(entry.id, lock).run();
  }
}

function requestSignal(signal: AbortSignal): AbortSignal {
  return AbortSignal.any([signal, AbortSignal.timeout(3_000)]);
}

async function segmentNonce(entryId: string, position: number): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${entryId}:${position}`));
  return btoa(String.fromCharCode(...new Uint8Array(digest, 0, 18))).replaceAll('+', '-').replaceAll('/', '_');
}
