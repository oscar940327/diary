import { Hono } from 'hono';
import { receiveDiscordInteraction, type DiscordBindings } from './discord';

const app = new Hono<{ Bindings: DiscordBindings }>();

app.onError((_error, c) => {
  console.error('INTERACTION_INTERNAL_ERROR');
  return c.text('Internal server error', 500);
});

app.post('/interactions', async (c) => {
  const result = await receiveDiscordInteraction(c.req.raw, c.env);
  if (result.status !== 200) {
    return c.text(result.message, result.status);
  }

  return c.json({ type: 1 });
});

app.all('/interactions', (c) => c.text('Method not allowed', 405, { Allow: 'POST' }));

export default app;
