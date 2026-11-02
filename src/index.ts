import { Hono } from 'hono';
import { receiveDiscordInteraction, type DiscordBindings } from './discord';

// Worker 的 HTTP 入口；Bindings 描述執行環境提供的設定。
const app = new Hono<{ Bindings: DiscordBindings }>();

// 只記錄通用原因碼，避免例外細節洩漏私人內容或憑證。
app.onError((_error, c) => {
  console.error('INTERACTION_INTERNAL_ERROR');
  return c.text('Internal server error', 500);
});

app.post('/interactions', async (c) => {
  // 將原始請求與環境設定交給驗證流程，再送出對應回覆。
  const result = await receiveDiscordInteraction(c.req.raw, c.env);
  if (result.status !== 200) {
    return c.text(result.message, result.status);
  }

  return c.json(result.response);
});

// 同一路徑只接受 POST；其他路徑由 Hono 預設回傳 404。
app.all('/interactions', (c) => c.text('Method not allowed', 405, { Allow: 'POST' }));

export default app;
