import {
  InteractionResponseFlags,
  InteractionResponseType,
  InteractionType,
  verifyKey,
} from 'discord-interactions';
import { captureRecord } from './record-capture';
import { maxRecordLength, validateRecordInput } from './record-input';

// 驗證請求與限制使用者所需的設定；ID 使用字串以保留精度。
type DiscordSettings = {
  DISCORD_PUBLIC_KEY: string;
  DISCORD_APPLICATION_ID: string;
  DISCORD_OWNER_ID: string;
  DISCORD_GUILD_ID: string;
};

// 環境可能缺少設定，因此收到請求後仍須檢查。
export type DiscordBindings = Partial<DiscordSettings> & { DB?: D1Database };
type VerifiedBindings = DiscordBindings & DiscordSettings;

type DiscordResponse =
  | { type: InteractionResponseType.PONG }
  | ReturnType<typeof recordForm>
  | {
    type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE;
    data: { flags: InteractionResponseFlags.EPHEMERAL };
  }
  | {
    type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE;
    data: { content: string; flags: InteractionResponseFlags.EPHEMERAL };
  };

// 成功交回 Discord 回覆內容，失敗交回 HTTP 狀態與通用訊息。
type InteractionResult =
  | { status: 200; response: DiscordResponse; afterResponse?: () => Promise<void> }
  | { status: 400 | 401 | 503; message: string };

type CommandData = { name: string; type: number };

const invalidInteraction = { status: 400, message: 'Invalid interaction' } as const;
const recordModalPrefix = 'record:';
const contentField = 'content';
const dateField = 'date';
const discordEpochMs = 1_420_070_400_000n;
const maxSnowflake = (1n << 64n) - 1n;

function recordForm(submissionId: string) {
  return {
    type: InteractionResponseType.MODAL as const,
    data: {
      custom_id: `${recordModalPrefix}${submissionId}`,
      title: '記錄日記',
      components: [
        {
          type: 18, // Label
          label: '日記內容',
          component: { type: 4, custom_id: contentField, style: 2, required: true, max_length: maxRecordLength },
        },
        {
          type: 18,
          label: '歸屬日期（選填）',
          component: {
            type: 4, custom_id: dateField, style: 1, required: false, max_length: 10, placeholder: 'YYYY-MM-DD',
          },
        },
      ],
    },
  };
}

// 確認是一般物件，才能安全讀取外部 JSON 的欄位。
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isSnowflake(value: unknown): value is string {
  return typeof value === 'string' && /^[1-9]\d{0,19}$/.test(value);
}

function snowflakeTime(value: unknown): Date | null {
  if (!isSnowflake(value)) return null;
  const snowflake = BigInt(value);
  if (snowflake > maxSnowflake) return null;
  return new Date(Number((snowflake >> 22n) + discordEpochMs));
}

function readRecordForm(data: unknown) {
  if (
    !isRecord(data) || typeof data.custom_id !== 'string'
    || !data.custom_id.startsWith(recordModalPrefix) || !Array.isArray(data.components)
  ) {
    return null;
  }

  const submissionId = data.custom_id.slice(recordModalPrefix.length);
  if (!isSnowflake(submissionId)) return null;

  let originalContent: string | undefined;
  let date: string | undefined;
  for (const label of data.components as unknown[]) {
    if (!isRecord(label) || label.type !== 18 || !isRecord(label.component) || label.component.type !== 4) {
      return null;
    }

    const input = label.component;
    if (input.custom_id === contentField && originalContent === undefined && typeof input.value === 'string') {
      originalContent = input.value;
    } else if (
      input.custom_id === dateField && date === undefined
      && (input.value === undefined || typeof input.value === 'string')
    ) {
      date = input.value ?? '';
    } else {
      return null;
    }
  }

  return originalContent === undefined ? null : { submissionId, originalContent, date: date ?? '' };
}

// 公開金鑰須為 32 bytes 的 hex，三個 ID 須為正整數字串。
function hasRequiredSettings(bindings: DiscordBindings): bindings is VerifiedBindings {
  const publicKey = bindings.DISCORD_PUBLIC_KEY;
  const ids = [
    bindings.DISCORD_APPLICATION_ID,
    bindings.DISCORD_OWNER_ID,
    bindings.DISCORD_GUILD_ID,
  ];

  return (
    typeof publicKey === 'string' && /^[a-f\d]{64}$/i.test(publicKey) &&
    ids.every((id) => typeof id === 'string' && /^[1-9]\d*$/.test(id))
  );
}

// 先檢查指令資料格式，再決定是否支援該指令。
function isCommandData(value: unknown): value is CommandData {
  return isRecord(value) &&
    typeof value.name === 'string' && value.name.trim().length > 0 &&
    typeof value.type === 'number' && Number.isInteger(value.type) && value.type > 0;
}

// 只採信已驗證請求的伺服器與操作者 ID，不依賴名稱或管理員權限。
function isOwner(interaction: Record<string, unknown>, settings: DiscordSettings): boolean {
  const member = interaction.member;
  return interaction.guild_id === settings.DISCORD_GUILD_ID && isRecord(member) &&
    isRecord(member.user) && member.user.id === settings.DISCORD_OWNER_ID;
}

// 統一加上 EPHEMERAL，讓文字回覆只對操作者可見。
function privateMessage(content: string): DiscordResponse {
  return {
    type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
    data: { content, flags: InteractionResponseFlags.EPHEMERAL },
  };
}

function commandResponse(data: CommandData): DiscordResponse {
  // 指令類型 1 是 slash command；其他類型即使同名也不執行。
  return privateMessage(data.type === 1 && data.name === 'ping' ? 'Pong!' : '不支援此指令');
}

function handleRecordSubmission(
  interaction: Record<string, unknown>,
  bindings: VerifiedBindings,
  receivedAt: Date,
): InteractionResult {
  const form = readRecordForm(interaction.data);
  const token = interaction.token;
  if (form === null || typeof token !== 'string' || token.length === 0) {
    return invalidInteraction;
  }

  if (!isOwner(interaction, bindings)) {
    return { status: 200, response: privateMessage('無法使用此指令') };
  }

  // 互動 ID 記載本次送出時間，表單 custom_id 內的 ID 則用於辨識重送。
  const submittedAt = snowflakeTime(interaction.id);
  if (submittedAt === null) return invalidInteraction;

  const input = validateRecordInput(form.originalContent, form.date, submittedAt);
  if (!input.ok) {
    return { status: 200, response: privateMessage(input.message) };
  }

  const db = bindings.DB;
  if (db === undefined) {
    const message = '日記未保存，資料庫尚未設定，請完成設定後重新送出。';
    return { status: 200, response: privateMessage(message) };
  }

  const submission = {
    applicationId: bindings.DISCORD_APPLICATION_ID,
    guildId: bindings.DISCORD_GUILD_ID,
    ownerId: bindings.DISCORD_OWNER_ID,
    submissionId: form.submissionId,
    originalContent: input.originalContent,
    requestedDate: input.requestedDate,
    entryDate: input.entryDate,
    createdAt: receivedAt.toISOString(),
  };
  return {
    status: 200,
    response: {
      type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
      data: { flags: InteractionResponseFlags.EPHEMERAL },
    },
    afterResponse: () => captureRecord(db, submission, token),
  };
}

// 處理順序：設定 → 簽章 → 內容 → 授權 → 指令回覆。
export async function receiveDiscordInteraction(
  request: Request,
  bindings: DiscordBindings,
): Promise<InteractionResult> {
  const receivedAt = new Date();
  if (!hasRequiredSettings(bindings)) {
    return { status: 503, message: 'Service unavailable' };
  }

  const signature = request.headers.get('x-signature-ed25519');
  const timestamp = request.headers.get('x-signature-timestamp');
  if (!signature || !/^[a-f\d]{128}$/i.test(signature) || !timestamp) {
    return { status: 401, message: 'Invalid request signature' };
  }

  // 必須驗證原始位元組；先解析再序列化可能改變簽章涵蓋的內容。
  const body = await request.arrayBuffer();
  if (!(await verifyKey(body, signature, timestamp, bindings.DISCORD_PUBLIC_KEY))) {
    return { status: 401, message: 'Invalid request signature' };
  }

  // 簽章通過後才解析；格式錯誤的 UTF-8 或 JSON 都回傳 400。
  let interaction: unknown;
  try {
    const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: false }).decode(body);
    interaction = JSON.parse(text);
  } catch {
    return invalidInteraction;
  }

  // 簽章有效仍須確認請求屬於目前的應用程式。
  if (!isRecord(interaction) || interaction.application_id !== bindings.DISCORD_APPLICATION_ID) {
    return invalidInteraction;
  }

  // Discord 驗證入口的 PING 沒有操作者資訊，須先於指令授權處理。
  if (interaction.type === InteractionType.PING) {
    return { status: 200, response: { type: InteractionResponseType.PONG } };
  }

  if (interaction.type === InteractionType.MODAL_SUBMIT) {
    return handleRecordSubmission(interaction, bindings, receivedAt);
  }

  if (
    interaction.type !== InteractionType.APPLICATION_COMMAND || !isCommandData(interaction.data)
  ) {
    return invalidInteraction;
  }

  // 200 表示成功回覆互動；訊息內容仍會拒絕未授權的使用者。
  if (!isOwner(interaction, bindings)) {
    return { status: 200, response: privateMessage('無法使用此指令') };
  }

  if (interaction.data.type === 1 && interaction.data.name === 'record') {
    if (!isSnowflake(interaction.id)) {
      return invalidInteraction;
    }
    if (bindings.DB === undefined) {
      const message = '日記功能尚未設定資料庫，請完成設定後再執行 /record。';
      return { status: 200, response: privateMessage(message) };
    }
    return { status: 200, response: recordForm(interaction.id) };
  }

  return { status: 200, response: commandResponse(interaction.data) };
}
