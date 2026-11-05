// 將金鑰與簽章轉成 Discord 標頭使用的十六進位格式。
function toHex(value: ArrayBuffer): string {
  return Array.from(new Uint8Array(value), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

// 產生測試專用金鑰與假 ID，不依賴真實 Discord 憑證。
export async function createDiscordFixture() {
  const keys = await crypto.subtle.generateKey('Ed25519', true, [
    'sign',
    'verify',
  ]) as CryptoKeyPair;

  const bindings = {
    DISCORD_PUBLIC_KEY: toHex(
      await crypto.subtle.exportKey('raw', keys.publicKey) as ArrayBuffer,
    ),
    DISCORD_APPLICATION_ID: '123456789012345678',
    DISCORD_OWNER_ID: '234567890123456789',
    DISCORD_GUILD_ID: '345678901234567890',
  };

  // 模擬 Discord 簽署「時間戳記 + 原始本文」，交給真正的驗證器檢查。
  async function signedRequest(body: string): Promise<Request> {
    // 固定時間方便重現；目前入口不檢查時間差或提供防重播保證。
    const timestamp = '1793491200';
    const signature = await crypto.subtle.sign(
      'Ed25519',
      keys.privateKey,
      new TextEncoder().encode(timestamp + body),
    );

    // Request 直接交給 Worker 測試入口，這個網址不會被送到網路上。
    return new Request('https://diary.test/interactions', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-signature-ed25519': toHex(signature),
        'x-signature-timestamp': timestamp,
      },
      body,
    });
  }

  return { bindings, signedRequest };
}
