import { version } from '../package.json';

export type DiaryChannel = { guildId: string; channelId: string; botToken: string };
export type DisplayFailure = 'permission' | 'channel' | 'rate-limit' | 'uncertain' | 'unknown' | 'timeout';
type Failure = { ok: false; reason: DisplayFailure };
const discordApi = 'https://discord.com/api/v10';

export function formatEntryMessages(date: string, original: string): string[] {
  // 紀錄上限為 4,000。至少吃掉半段，段號與總數皆只需一位數。
  const capacity = 2_000 - `${date}（1/1）\n`.length;
  const parts: string[] = [];
  let start = 0;
  while (start < original.length) {
    let end = Math.min(start + capacity, original.length);
    if (end < original.length) {
      const next = original.charCodeAt(end);
      if (next >= 0xDC00 && next <= 0xDFFF) end--;
      const newline = original.lastIndexOf('\n', end - 1);
      if (newline >= start + Math.floor(capacity / 2)) end = newline + 1;
    }
    parts.push(original.slice(start, end));
    start = end;
  }
  return parts.map((part, index) => `${date}（${index + 1}/${parts.length}）\n${part}`);
}

export async function verifyDiaryChannel(
  target: DiaryChannel, signal: AbortSignal,
): Promise<{ ok: true; channel: DiaryChannel } | Failure> {
  try {
    const response = await channelRequest(target, '', signal);
    if (!response.ok) return failure(response, false);
    const channel = await response.json<{ id?: unknown; guild_id?: unknown; type?: unknown }>();
    return channel?.id === target.channelId && channel.guild_id === target.guildId && channel.type === 0
      ? { ok: true, channel: target }
      : { ok: false, reason: 'channel' };
  } catch {
    return { ok: false, reason: signal.aborted ? 'timeout' : 'unknown' };
  }
}

export async function sendEntryMessage(
  channel: DiaryChannel, content: string, nonce: string, signal: AbortSignal,
): Promise<{ ok: true; messageId: string } | Failure> {
  try {
    const response = await channelRequest(channel, '/messages', signal, JSON.stringify({
      content, nonce, enforce_nonce: true, allowed_mentions: { parse: [] }, flags: 4,
    }));
    if (!response.ok) return failure(response, true);
    const message = await response.json<{ id?: unknown; channel_id?: unknown }>();
    if (message?.channel_id !== channel.channelId || typeof message.id !== 'string' || !/^[1-9]\d{0,19}$/.test(message.id)) {
      return { ok: false, reason: 'uncertain' };
    }
    return { ok: true, messageId: message.id };
  } catch {
    return { ok: false, reason: 'uncertain' };
  }
}

function channelRequest(target: DiaryChannel, path: string, signal: AbortSignal, body?: string): Promise<Response> {
  signal.throwIfAborted();
  return fetch(`${discordApi}/channels/${encodeURIComponent(target.channelId)}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      'content-type': 'application/json',
      'user-agent': `DiscordBot (https://github.com/oscar940327/diary, ${version})`,
      authorization: `Bot ${target.botToken}`,
    },
    ...(body === undefined ? {} : { body }),
    cache: 'no-store',
    redirect: 'error',
    signal,
  });
}

async function failure(response: Response, posting: boolean): Promise<Failure> {
  if (response.status === 429) return { ok: false, reason: 'rate-limit' };
  if (response.status === 403 && posting) {
    const details = await response.json<{ code?: unknown }>().catch(() => null);
    return { ok: false, reason: details?.code === 50013 ? 'permission' : 'channel' };
  }
  if ([401, 403, 404].includes(response.status)) return { ok: false, reason: 'channel' };
  return { ok: false, reason: posting && (response.status >= 500 || response.status === 408) ? 'uncertain' : 'unknown' };
}
