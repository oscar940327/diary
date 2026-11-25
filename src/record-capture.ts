import { saveEntry, type EntrySubmission } from './entry-storage';

export async function captureRecord(
  db: D1Database,
  submission: EntrySubmission,
  interactionToken: string,
): Promise<void> {
  let content: string;
  try {
    const result = await saveEntry(db, submission);
    content = result.status === 'conflict'
      ? '日記未保存，這次提交已有不同的內容或日期，請重新開啟表單。'
      : '日記已保存。';
  } catch (error) {
    content = saveFailureMessage(error);
  }

  try {
    // 更新原本的延後回覆，沿用只有操作者能看到的設定。
    const token = encodeURIComponent(interactionToken);
    const url = `https://discord.com/api/v10/webhooks/${submission.applicationId}/${token}/messages/@original`;
    const signal = AbortSignal.timeout(4000);
    const updateReply = () => fetch(url, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content, allowed_mentions: { parse: [] } }),
      redirect: 'error',
      signal,
    });
    let response = await updateReply();
    if (response.status === 404) {
      // D1 很快完成時，Discord 可能還沒建立原始回覆。同一則回覆只補試一次。
      await new Promise<void>(resolve => setTimeout(resolve, 200));
      response = await updateReply();
    }
    if (!response.ok) console.error('RECORD_REPLY_UPDATE_FAILED');
  } catch {
    console.error('RECORD_REPLY_UPDATE_FAILED');
  }
}

function saveFailureMessage(error: unknown): string {
  // D1 明確回報資料表不存在時，寫入無法執行。其他錯誤可能發生在寫入後。
  if (
    error instanceof Error
    && /^D1_ERROR: no such table: (?:main\.)?entries(?:: SQLITE_ERROR)?$/.test(error.message)
  ) {
    return '日記未保存，資料庫尚未初始化，請套用資料表遷移後重新送出。';
  }
  return '日記保存結果未確認，暫時無法查證資料庫狀態，請保留原文並先確認本次紀錄。';
}
