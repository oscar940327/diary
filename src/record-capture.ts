import { InteractionResponseFlags, InteractionResponseType } from 'discord-interactions';
import { version } from '../package.json';
import { EntryInsertError, findEntryById, findEntryBySubmission, isDailyQuotaError, saveEntry, type Entry, type EntryScope, type EntrySubmission } from './entry-storage';
import { publishEntry } from './publish-entry';
import type { DiaryChannel, DisplayFailure } from './entry-display';

const acknowledgmentDeadlineMs = 2_000;
const saveDeadlineMs = 12_000;
const workDeadlineMs = 24_000; // 加上私人結果的 4 秒，仍低於 waitUntil 的 30 秒。
const replyDeadlineMs = 4_000;
const temporaryReplyStatuses = new Set([500, 502, 503, 504]);
const privateLoadingFlags = InteractionResponseFlags.EPHEMERAL | (1 << 7); // Discord 的 LOADING 旗標
const discordHeaders = {
  'content-type': 'application/json',
  'user-agent': `DiscordBot (https://github.com/oscar940327/diary, ${version})`,
};

type RecordInteraction = { id: string; token: string };
type PrivateReply = { content: string; retry?: string };
export type RetryTarget = { kind: 'entry' | 'submission'; id: string };

export async function captureRecord(
  db: D1Database,
  submission: EntrySubmission,
  interaction: RecordInteraction,
  target: DiaryChannel,
): Promise<void> {
  return runRecordOperation(submission.applicationId, interaction, async signal => {
    let result: Awaited<ReturnType<typeof saveEntry>>;
    const saveDeadline = new AbortController();
    // 停止等待不會取消 D1 寫入。用同一提交識別查證，避免要求重新新增。
    const timeout = setTimeout(() => saveDeadline.abort(), saveDeadlineMs);
    try {
      result = await beforeAbort(
        saveEntry(db, submission), AbortSignal.any([signal, saveDeadline.signal]),
      );
    } catch (error) {
      return saveFailureReply(error, submission.submissionId);
    } finally {
      clearTimeout(timeout);
    }
    if (result.status === 'conflict') {
      return { content: '日記未保存，這次提交已有不同的內容或日期，請重新開啟表單。' };
    }
    return displaySavedEntry(db, result.entry, target, signal);
  });
}

export async function retryRecord(
  db: D1Database, scope: EntryScope, selected: RetryTarget, interaction: RecordInteraction, target: DiaryChannel,
): Promise<void> {
  return runRecordOperation(scope.applicationId, interaction, async signal => {
    const retry = `retry:${selected.kind}:${selected.id}`;
    let entry: Entry | null;
    try {
      entry = await beforeAbort(selected.kind === 'entry'
        ? findEntryById(db, scope, selected.id)
        : findEntryBySubmission(db, { ...scope, submissionId: selected.id }), signal);
    } catch (error) {
      return { content: unconfirmedSaveMessage(error), retry };
    }
    if (!entry) {
      return {
        content: selected.kind === 'submission'
          ? '目前找不到這次提交的日記，請保留原文、確認尚未保存後再重新填寫。'
          : '目前找不到可重試的日記，請確認紀錄後再操作。',
      };
    }
    return displaySavedEntry(db, entry, target, signal);
  });
}

async function displaySavedEntry(db: D1Database, entry: Entry, target: DiaryChannel, signal: AbortSignal): Promise<PrivateReply> {
  const retry = `retry:entry:${entry.id}`;
  try {
    signal.throwIfAborted();
    const result = await beforeAbort(publishEntry(db, entry, target, signal), signal);
    if (result.status === 'sent') return { content: '日記已保存並已顯示。' };
    if (result.status === 'busy') return { content: '日記已保存，正在處理顯示，請稍後確認結果。', retry };
    return { content: displayFailureMessage(result.reason, result.uncertain === true), retry };
  } catch {
    console.error('RECORD_DISPLAY_PROGRESS_UNAVAILABLE');
    return { content: displayFailureMessage(signal.aborted ? 'timeout' : 'unknown', true), retry };
  }
}

function displayFailureMessage(reason: DisplayFailure, uncertain: boolean): string {
  if (reason === 'uncertain') {
    return '日記已保存，但部分訊息可能已送達，請先查看日記頻道再決定是否重試顯示。';
  }
  const [detail, nextStep] = {
    permission: ['機器人沒有頻道發言權限', '開啟權限後重試顯示'],
    channel: ['無法存取設定的日記頻道', '確認頻道與 Bot 權限後重試顯示'],
    'rate-limit': ['Discord 暫時限制發送', '稍後重試顯示'],
    unknown: ['顯示失敗且原因暫不明', '稍後重試顯示'],
    timeout: ['顯示作業逾時', '稍後重試顯示'],
  }[reason] as [string, string];
  const advisory = uncertain ? '，部分訊息可能已送達，請先查看日記頻道，再' : '，請';
  return `日記已保存，但${detail}${advisory}${nextStep}。`;
}

async function beforeAbort<T>(operation: Promise<T>, signal: AbortSignal): Promise<T> {
  const abort = Promise.withResolvers<never>();
  const onAbort = () => abort.reject(signal.reason);
  signal.addEventListener('abort', onAbort, { once: true });
  if (signal.aborted) onAbort();
  try {
    return await Promise.race([operation, abort.promise]);
  } finally {
    signal.removeEventListener('abort', onAbort);
  }
}

async function runRecordOperation(
  applicationId: string, interaction: RecordInteraction, operation: (signal: AbortSignal) => Promise<PrivateReply>,
): Promise<void> {
  const signal = AbortSignal.timeout(workDeadlineMs);
  const token = encodeURIComponent(interaction.token);
  const replyUrl = `https://discord.com/api/v10/webhooks/${applicationId}/${token}/messages/@original`;
  if (!(await acknowledgeRecord(interaction.id, token, replyUrl))) {
    console.error('RECORD_ACKNOWLEDGMENT_FAILED');
    return;
  }

  try {
    const reply = await operation(signal);
    if (!(await updatePrivateReply(replyUrl, reply))) console.error('RECORD_REPLY_UPDATE_FAILED');
  } catch {
    console.error('RECORD_REPLY_UPDATE_FAILED');
  }
}

async function updatePrivateReply(replyUrl: string, reply: PrivateReply): Promise<boolean> {
  // 等待和重試都共用同一個期限，且只更新原本的私人回覆。
  const deadline = performance.now() + replyDeadlineMs;
  const signal = AbortSignal.timeout(replyDeadlineMs);
  const request: RequestInit = {
    method: 'PATCH',
    headers: discordHeaders,
    body: JSON.stringify({
      content: reply.content, allowed_mentions: { parse: [] },
      ...(reply.retry === undefined ? {} : {
        components: [{ type: 1, components: [{ type: 2, style: 2, label: '重試顯示', custom_id: reply.retry }] }],
      }),
    }),
    redirect: 'error',
    signal,
  };
  let backoffMs = 200;
  for (;;) {
    signal.throwIfAborted();
    let response: Response | undefined;
    try {
      response = await fetch(replyUrl, request);
    } catch (error) {
      if (!(error instanceof TypeError) || signal.aborted) throw error;
    }

    if (response?.ok) return true;
    let waitMs = backoffMs;
    if (response?.status === 429) {
      const retryAfterMs = await readRetryAfterMs(response);
      if (retryAfterMs === null) return false;
      waitMs = Math.max(backoffMs, retryAfterMs);
    } else if (response && !temporaryReplyStatuses.has(response.status)) {
      return false;
    }

    if (waitMs >= deadline - performance.now()) return false;
    await scheduler.wait(waitMs, { signal });
    backoffMs = Math.min(backoffMs * 2, 1_000);
  }
}

async function readRetryAfterMs(response: Response): Promise<number | null> {
  const header = response.headers.get('retry-after')?.trim();
  if (header && /^\d+(?:\.\d+)?$/.test(header)) {
    return Math.ceil(Number(header) * 1_000);
  }
  const details = await response.json<{ retry_after?: unknown }>();
  const seconds = details?.retry_after;
  return typeof seconds === 'number' && Number.isFinite(seconds) && seconds >= 0
    ? Math.ceil(seconds * 1_000)
    : null;
}

async function acknowledgeRecord(interactionId: string, encodedToken: string, replyUrl: string): Promise<boolean> {
  try {
    const signal = AbortSignal.timeout(acknowledgmentDeadlineMs);
    const response = await fetch(`https://discord.com/api/v10/interactions/${interactionId}/${encodedToken}/callback`, {
      method: 'POST',
      headers: discordHeaders,
      body: JSON.stringify({
        type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
        data: { flags: InteractionResponseFlags.EPHEMERAL },
      }),
      redirect: 'error',
      signal,
    });
    if (response.status === 204) return true;
    if (response.status !== 400) return false;
    const failure = await response.json<{ code?: unknown }>();
    if (failure?.code !== 40060) return false;

    // 重送時只在原本的回覆仍是私人「處理中」時繼續保存。
    signal.throwIfAborted();
    const original = await fetch(replyUrl, {
      method: 'GET', headers: discordHeaders, cache: 'no-store', redirect: 'error', signal,
    });
    if (original.status !== 200) return false;
    const message = await original.json<{ flags?: unknown }>();
    const flags = message?.flags;
    return typeof flags === 'number' && Number.isSafeInteger(flags) && flags >= 0
      && (flags & privateLoadingFlags) === privateLoadingFlags;
  } catch {
    return false;
  }
}

function saveFailureReply(error: unknown, submissionId: string): PrivateReply {
  // 重送時若查不到既有紀錄的結果，仍無法確定這份表單是否已保存。
  if (error instanceof EntryInsertError) {
    if (/^D1_ERROR: no such table: (?:main\.)?entries(?:: SQLITE_ERROR)?$/.test(error.message)) {
      return { content: '日記未保存，資料庫尚未初始化，請套用資料表遷移後重新送出。' };
    }
    if (error.quota === 'daily') {
      return { content: '日記未保存，資料庫每日額度已用完，請保留原文並等額度重置後再送出。' };
    }
    if (error.quota === 'storage') {
      return { content: '日記未保存，資料庫儲存空間已達上限，請保留原文並在釋出空間後再送出。' };
    }
  }
  return { content: unconfirmedSaveMessage(error), retry: `retry:submission:${submissionId}` };
}

function unconfirmedSaveMessage(error: unknown): string {
  return isDailyQuotaError(error)
    ? '日記保存結果未確認，資料庫每日額度已用完，請保留原文並在額度重置後重試顯示以確認本次紀錄。'
    : '日記保存結果未確認，暫時無法查證資料庫狀態，請保留原文並稍後按重試顯示確認本次紀錄。';
}
