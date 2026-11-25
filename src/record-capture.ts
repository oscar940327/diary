import { InteractionResponseFlags, InteractionResponseType } from 'discord-interactions';
import { EntryInsertError, saveEntry, type EntrySubmission } from './entry-storage';

const acknowledgmentDeadlineMs = 2_000;
const saveDeadlineMs = 20_000;
const replyDeadlineMs = 4_000;

type RecordInteraction = { id: string; token: string };

export async function captureRecord(
  db: D1Database,
  submission: EntrySubmission,
  interaction: RecordInteraction,
): Promise<void> {
  const token = encodeURIComponent(interaction.token);
  if (!(await acknowledgeRecord(interaction.id, token))) {
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
    // 更新原本的延後回覆，沿用只有操作者能看到的設定。
    const url = `https://discord.com/api/v10/webhooks/${submission.applicationId}/${token}/messages/@original`;
    const response = await fetch(url, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content, allowed_mentions: { parse: [] } }),
      redirect: 'error',
      signal: AbortSignal.timeout(replyDeadlineMs),
    });
    if (!response.ok) console.error('RECORD_REPLY_UPDATE_FAILED');
  } catch {
    console.error('RECORD_REPLY_UPDATE_FAILED');
  }
}

async function acknowledgeRecord(interactionId: string, encodedToken: string): Promise<boolean> {
  try {
    const response = await fetch(`https://discord.com/api/v10/interactions/${interactionId}/${encodedToken}/callback`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
        data: { flags: InteractionResponseFlags.EPHEMERAL },
      }),
      redirect: 'error',
      signal: AbortSignal.timeout(acknowledgmentDeadlineMs),
    });
    return response.status === 204;
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
    if (/^D1_ERROR: Your account has exceeded D1's free tier daily row (?:read|write) limit(?:\.|$)/.test(error.message)) {
      return '日記未保存，資料庫每日額度已用完，請保留原文並等額度重置後再送出。';
    }
    if (
      /^D1_ERROR: Your account has exceeded D1's maximum account storage limit(?:\.|$)/.test(error.message)
      || /^D1_ERROR: Exceeded maximum DB size(?:\.|$)/.test(error.message)
    ) {
      return '日記未保存，資料庫儲存空間已達上限，請保留原文並在釋出空間後再送出。';
    }
  }
  return '日記保存結果未確認，暫時無法查證資料庫狀態，請保留原文並先確認本次紀錄。';
}
