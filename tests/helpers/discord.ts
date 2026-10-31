function toHex(value: ArrayBuffer): string {
  return Array.from(new Uint8Array(value), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

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

  async function signedRequest(body: string): Promise<Request> {
    const timestamp = '1793491200';
    const signature = await crypto.subtle.sign(
      'Ed25519',
      keys.privateKey,
      new TextEncoder().encode(timestamp + body),
    );

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
