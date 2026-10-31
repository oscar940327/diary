import { verifyKey } from 'discord-interactions';

type DiscordSettings = {
  DISCORD_PUBLIC_KEY: string;
  DISCORD_APPLICATION_ID: string;
  DISCORD_OWNER_ID: string;
  DISCORD_GUILD_ID: string;
};

export type DiscordBindings = Partial<DiscordSettings>;

type InteractionResult =
  | { status: 200 }
  | { status: 400 | 401 | 503; message: string };

function hasRequiredSettings(bindings: DiscordBindings): bindings is DiscordSettings {
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

export async function receiveDiscordInteraction(
  request: Request,
  bindings: DiscordBindings,
): Promise<InteractionResult> {
  if (!hasRequiredSettings(bindings)) {
    return { status: 503, message: 'Service unavailable' };
  }

  const signature = request.headers.get('x-signature-ed25519');
  const timestamp = request.headers.get('x-signature-timestamp');
  if (!signature || !/^[a-f\d]{128}$/i.test(signature) || !timestamp) {
    return { status: 401, message: 'Invalid request signature' };
  }

  const body = await request.arrayBuffer();
  if (!(await verifyKey(body, signature, timestamp, bindings.DISCORD_PUBLIC_KEY))) {
    return { status: 401, message: 'Invalid request signature' };
  }

  let interaction: unknown;
  try {
    const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: false }).decode(body);
    interaction = JSON.parse(text);
  } catch {
    return { status: 400, message: 'Invalid interaction' };
  }

  if (
    interaction === null || typeof interaction !== 'object' || Array.isArray(interaction) ||
    !('application_id' in interaction) || interaction.application_id !== bindings.DISCORD_APPLICATION_ID ||
    !('type' in interaction) || interaction.type !== 1
  ) {
    return { status: 400, message: 'Invalid interaction' };
  }

  return { status: 200 };
}
