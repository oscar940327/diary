type Environment = 'test' | 'production';
type RegistrationSummary = {
  environment: Environment;
  applicationId: string;
  guildId: string;
  command: 'ping';
  dryRun: boolean;
};

// 只有工具自己產生的訊息可以送到終端機，避免外部錯誤夾帶 token。
class RegistrationError extends Error {}

// 沒有預設環境；未知、缺漏或重複參數都停止處理。
function parseArguments(args: string[]): { environment: Environment; dryRun: boolean } {
  let environment: Environment | undefined;
  let dryRun = false;
  const argumentError = () => new RegistrationError(
    '參數無效：請指定 --env test 或 --env production，可加 --dry-run。',
  );

  for (let index = 0; index < args.length; index++) {
    if (args[index] === '--env' && environment === undefined) {
      const value = args[++index];
      if (value !== 'test' && value !== 'production') throw argumentError();
      environment = value;
    } else if (args[index] === '--dry-run' && !dryRun) {
      dryRun = true;
    } else {
      throw argumentError();
    }
  }
  if (environment === undefined) throw argumentError();
  return { environment, dryRun };
}

// 只讀選定環境的設定，不回退到通用名稱或另一個環境。
function registrationSettings(environment: Environment, env: Record<string, string | undefined>) {
  const prefix = `DISCORD_${environment.toUpperCase()}`;
  const applicationId = env[`${prefix}_APPLICATION_ID`];
  const guildId = env[`${prefix}_GUILD_ID`];
  const token = env[`${prefix}_BOT_TOKEN`];
  if (
    !applicationId || !/^[1-9]\d*$/.test(applicationId) ||
    !guildId || !/^[1-9]\d*$/.test(guildId) || !token || /\s/.test(token)
  ) {
    throw new RegistrationError('環境設定不完整或無效，請檢查選定環境的 APPLICATION_ID、GUILD_ID 與 BOT_TOKEN。');
  }
  if (
    env.DISCORD_TEST_APPLICATION_ID === env.DISCORD_PRODUCTION_APPLICATION_ID ||
    env.DISCORD_TEST_BOT_TOKEN === env.DISCORD_PRODUCTION_BOT_TOKEN
  ) {
    throw new RegistrationError('環境設定無效：測試與正式不可共用應用程式 ID 或 Bot token。');
  }
  return { applicationId, guildId, token };
}

// 對外入口只回傳不含 token 的摘要；dry run 在發送 HTTP 之前結束。
export async function runRegistration(
  args: string[],
  env: Record<string, string | undefined>,
): Promise<RegistrationSummary> {
  const { environment, dryRun } = parseArguments(args);
  const { applicationId, guildId, token } = registrationSettings(environment, env);
  const summary: RegistrationSummary = { environment, applicationId, guildId, command: 'ping', dryRun };
  if (dryRun) return summary;

  let response: Response;
  try {
    // 單一 guild command 的 POST 會建立或更新同名指令，不覆寫其他指令。
    response = await fetch(
      `https://discord.com/api/v10/applications/${applicationId}/guilds/${guildId}/commands`,
      {
        method: 'POST', redirect: 'error',
        headers: { Authorization: `Bot ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'ping', type: 1, description: '確認 Diary 後端連通' }),
      },
    );
  } catch {
    throw new RegistrationError('指令註冊失敗，請檢查網路與選定環境設定。');
  }
  if (response.status !== 200 && response.status !== 201) {
    throw new RegistrationError(`指令註冊失敗（HTTP ${response.status}）。`);
  }
  return summary;
}

// Node.js 24 可直接執行此 TypeScript；被測試匯入時不啟動 CLI。
if (import.meta.main) {
  try {
    console.log(JSON.stringify(await runRegistration(process.argv.slice(2), process.env)));
  } catch (error) {
    console.error(error instanceof RegistrationError ? error.message : '指令註冊失敗。');
    process.exitCode = 1;
  }
}
