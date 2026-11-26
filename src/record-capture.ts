import { InteractionResponseFlags, InteractionResponseType } from 'discord-interactions';
import { version } from '../package.json';
import { EntryInsertError, saveEntry, type EntrySubmission } from './entry-storage';

const acknowledgmentDeadlineMs = 2_000;
const saveDeadlineMs = 20_000;
const replyDeadlineMs = 4_000;
const temporaryReplyStatuses = new Set([500, 502, 503, 504]);
const privateLoadingFlags = InteractionResponseFlags.EPHEMERAL | (1 << 7); // Discord 的 LOADING 旗標
const discordHeaders = {
  'content-type': 'application/json',
  'user-agent': `DiscordBot (https://github.com/oscar940327/diary, ${version})`,
};

type RecordInteraction = { id: string; token: string };

export async function captureRecord(
  db: D1Database,
  submission: EntrySubmission,
  interaction: RecordInteraction,
): Promise<void> {
  const token = encodeURIComponent(interaction.token);
  const replyUrl = `https://discord.com/api/v10/webhooks/${submission.applicationId}/${token}/messages/@original`;
  if (!(await acknowledgeRecord(interaction.id, token, replyUrl))) {
    console.error('RECORD_ACKNOWLEDGMENT_FAILED');
    return;
  }

  const deadline = Promise.withResolvers<never>();
  // 停止等待不會取消 D1 寫入。先保留時間更新 Discord 的私人回覆。
  const timeout = setTimeout(() => deadline.reject(new Error('D1 save wait expired')), saveDeadlineMs);
  let content: string;
  try {
    const result = await Promise.race([saveEntry(db, submission), deadline.promise]);
    content = result.status === 'conflict'
      ? '日記未保存，這次提交已有不同的內容或日期，請重新開啟表單。'
      : '日記已保存。';
  } catch (error) {
    content = saveFailureMessage(error);
  } finally {
    clearTimeout(timeout);
  }

  try {
    if (!(await updatePrivateReply(replyUrl, content))) console.error('RECORD_REPLY_UPDATE_FAILED');
  } catch {
    console.error('RECORD_REPLY_UPDATE_FAILED');
  }
}

async function updatePrivateReply(replyUrl: string, content: string): Promise<boolean> {
  // 等待和重試都共用同一個期限，且只更新原本的私人回覆。
  const deadline = performance.now() + replyDeadlineMs;
  const signal = AbortSignal.timeout(replyDeadlineMs);
  const request: RequestInit = {
    method: 'PATCH',
    headers: discordHeaders,
    body: JSON.stringify({ content, allowed_mentions: { parse: [] } }),
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

function saveFailureMessage(error: unknown): string {
  // 重送時若查不到既有紀錄的結果，仍無法確定這份表單是否已保存。
  if (error instanceof EntryInsertError) {
    if (/^D1_ERROR: no such table: (?:main\.)?entries(?:: SQLITE_ERROR)?$/.test(error.message)) {
      return '日記未保存，資料庫尚未初始化，請套用資料表遷移後重新送出。';
    }
    if (error.quota === 'daily') {
      return '日記未保存，資料庫每日額度已用完，請保留原文並等額度重置後再送出。';
    }
    if (error.quota === 'storage') {
      return '日記未保存，資料庫儲存空間已達上限，請保留原文並在釋出空間後再送出。';
    }
  }
  return '日記保存結果未確認，暫時無法查證資料庫狀態，請保留原文並先確認本次紀錄。';
}
