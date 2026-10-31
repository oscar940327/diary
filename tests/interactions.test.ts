import { beforeAll, describe, expect, it, vi } from 'vitest';
import worker from '../src/index';
import { createDiscordFixture } from './helpers/discord';

describe('Discord HTTP interaction endpoint', () => {
  let discord: Awaited<ReturnType<typeof createDiscordFixture>>;

  beforeAll(async () => {
    discord = await createDiscordFixture();
  });

  it('acknowledges a signed protocol PING without user or guild fields', async () => {
    const request = await discord.signedRequest(JSON.stringify({
      application_id: discord.bindings.DISCORD_APPLICATION_ID,
      type: 1,
    }));

    const response = await worker.fetch(request, discord.bindings);

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');
    expect(await response.json()).toEqual({ type: 1 });
  });

  it('rejects a request without a Discord signature', async () => {
    const response = await worker.fetch(new Request('https://diary.test/interactions', {
      method: 'POST',
      body: JSON.stringify({ application_id: discord.bindings.DISCORD_APPLICATION_ID, type: 1 }),
    }), discord.bindings);

    expect(response.status).toBe(401);
  });

  it('rejects a forged signature instead of acknowledging PING', async () => {
    const request = await discord.signedRequest(JSON.stringify({
      application_id: discord.bindings.DISCORD_APPLICATION_ID,
      type: 1,
    }));
    request.headers.set('x-signature-ed25519', '00'.repeat(64));

    const response = await worker.fetch(request, discord.bindings);

    expect(response.status).toBe(401);
  });

  it.each(['x-signature-ed25519', 'x-signature-timestamp'])(
    'rejects a request missing only %s',
    async (header) => {
      const request = await discord.signedRequest('{"type":1}');
      request.headers.delete(header);

      expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
    },
  );

  it.each(['not-hex', '01', ''])('rejects a malformed signature: %j', async (signature) => {
    const request = await discord.signedRequest('{"type":1}');
    request.headers.set('x-signature-ed25519', signature);

    expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
  });

  it('rejects a body changed after signing, before trying to parse it', async () => {
    const original = await discord.signedRequest('{"type":1}');
    const request = new Request(original, { body: 'tampered, not JSON' });

    expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
  });

  it('rejects non-hex text even when a permissive parser could recover valid signature bytes', async () => {
    for (let nonce = 0; nonce < 100; nonce++) {
      const request = await discord.signedRequest(JSON.stringify({
        application_id: discord.bindings.DISCORD_APPLICATION_ID,
        type: 1,
        nonce,
      }));
      const bytes = request.headers.get('x-signature-ed25519')!.match(/../g)!;
      const index = bytes.findIndex((byte) => byte.startsWith('0'));
      if (index === -1) continue;

      // For example, the malformed pair "ag" must not be accepted as the byte 0x0a.
      bytes[index] = `${bytes[index]![1]}g`;
      request.headers.set('x-signature-ed25519', bytes.join(''));

      expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
      return;
    }

    throw new Error('Could not construct a non-hex signature fixture');
  });

  it('rejects a timestamp changed after signing', async () => {
    const request = await discord.signedRequest('{"type":1}');
    request.headers.set('x-signature-timestamp', '1793491201');

    expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
  });

  it('rejects a signature from a different application key', async () => {
    const other = await createDiscordFixture();
    const request = await other.signedRequest('{"type":1}');

    expect((await worker.fetch(request, discord.bindings)).status).toBe(401);
  });

  it('preserves whitespace and Traditional Chinese in the signed body', async () => {
    const body = ` {\n  "application_id": "${discord.bindings.DISCORD_APPLICATION_ID}",\n  "type": 1,\n  "note": "今天記錄生活 🌱"\n}\n`;
    const response = await worker.fetch(await discord.signedRequest(body), discord.bindings);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ type: 1 });
  });

  it('returns 503 when the application public key is missing', async () => {
    const request = await discord.signedRequest('{"type":1}');

    expect((await worker.fetch(request, {})).status).toBe(503);
  });

  it.each(['DISCORD_APPLICATION_ID', 'DISCORD_OWNER_ID', 'DISCORD_GUILD_ID'] as const)(
    'returns 503 when %s is missing',
    async (setting) => {
      const bindings: Partial<typeof discord.bindings> = { ...discord.bindings };
      delete bindings[setting];

      const response = await worker.fetch(await discord.signedRequest('{"type":1}'), bindings);

      expect(response.status).toBe(503);
    },
  );

  it.each([
    ['DISCORD_PUBLIC_KEY', 'not-a-public-key'],
    ['DISCORD_PUBLIC_KEY', 'gg'.repeat(32)],
    ['DISCORD_APPLICATION_ID', ''],
    ['DISCORD_APPLICATION_ID', '123 456'],
    ['DISCORD_OWNER_ID', 'owner-name'],
    ['DISCORD_GUILD_ID', '-123'],
  ] as const)('returns 503 for invalid %s: %j', async (setting, value) => {
    const request = await discord.signedRequest('{"type":1}');
    const bindings = { ...discord.bindings, [setting]: value };

    const response = await worker.fetch(request, bindings);

    expect(response.status).toBe(503);
    expect(await response.text()).toBe('Service unavailable');
  });

  it.each([
    ['non-JSON', '{'],
    ['empty body', ''],
    ['null', 'null'],
    ['array', '[]'],
    ['primitive', '"ping"'],
    ['missing application ID', '{"type":1}'],
    ['wrong application ID', '{"application_id":"999999999999999999","type":1}'],
    ['missing type', '{"application_id":"123456789012345678"}'],
    ['text instead of numeric type', '{"application_id":"123456789012345678","type":"1"}'],
    ['unsupported interaction type', '{"application_id":"123456789012345678","type":999}'],
    ['unsupported message component', '{"application_id":"123456789012345678","type":3}'],
  ] as const)('rejects signed invalid input: %s', async (_label, body) => {
    const response = await worker.fetch(await discord.signedRequest(body), discord.bindings);

    expect(response.status).toBe(400);
    expect(await response.text()).toBe('Invalid interaction');
  });

  it.each(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])(
    'returns 405 and allows only POST for %s /interactions',
    async (method) => {
      const response = await worker.fetch(new Request('https://diary.test/interactions', {
        method,
      }), {});

      expect(response.status).toBe(405);
      expect(response.headers.get('allow')).toBe('POST');
    },
  );

  it.each(['/', '/missing', '/interactions/extra'])('returns 404 for %s', async (path) => {
    const response = await worker.fetch(new Request(`https://diary.test${path}`), {});

    expect(response.status).toBe(404);
  });

  it('keeps unexpected body-read errors out of responses and application logs', async () => {
    const privateDetail = 'private-body-and-interaction-token';
    const errorLog = vi.spyOn(console, 'error').mockImplementation(() => {});

    try {
      const request = new Request('https://diary.test/interactions', {
        method: 'POST',
        headers: {
          'x-signature-ed25519': '00'.repeat(64),
          'x-signature-timestamp': '1793491200',
        },
        body: new ReadableStream({
          pull(controller) {
            controller.error(new Error(privateDetail));
          },
        }),
      });

      const response = await worker.fetch(request, discord.bindings);

      expect(response.status).toBe(500);
      expect(await response.text()).not.toContain(privateDetail);
      expect(errorLog.mock.calls.flat().map(String).join(' ')).not.toContain(privateDetail);
    } finally {
      errorLog.mockRestore();
    }
  });
});
