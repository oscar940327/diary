export const maxRecordLength = 4000;

const taipeiCalendar = new Intl.DateTimeFormat('en', {
  timeZone: 'Asia/Taipei',
  calendar: 'gregory',
  numberingSystem: 'latn',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

type RecordInputResult =
  | { ok: true; originalContent: string; requestedDate: string | null; entryDate: string }
  | { ok: false; message: string };

export function validateRecordInput(
  originalContent: string,
  rawDate: string,
  submittedAt: Date,
): RecordInputResult {
  if (originalContent.trim().length === 0) {
    return { ok: false, message: '日記未保存，內容是空白，請輸入內容後重新送出。' };
  }
  if (originalContent.length > maxRecordLength) {
    return { ok: false, message: '日記未保存，內容最多 4,000 字元，請縮短後重新送出。' };
  }

  const requestedDate = rawDate.trim() || null;
  if (requestedDate !== null && !isCalendarDate(requestedDate)) {
    return { ok: false, message: '日記未保存，日期無效，請輸入 YYYY-MM-DD 格式的有效日期後重新送出。' };
  }

  const parts = Object.fromEntries(taipeiCalendar.formatToParts(submittedAt).map(({ type, value }) => [type, value]));
  const today = `${parts.year}-${parts.month}-${parts.day}`;
  if (requestedDate !== null && requestedDate > today) {
    return { ok: false, message: '日記未保存，日期晚於台北時間的今天，請改填今天或過去的日期。' };
  }

  return { ok: true, originalContent, requestedDate, entryDate: requestedDate ?? today };
}

function isCalendarDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000-')) return false;

  // 使用明確的 UTC 格式，再比對原日期以拒絕自動進位的無效日期。
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}
