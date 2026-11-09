# Discord Bot 操作說明

本文件對應 `bootstrap-discord-bot`。Stage 4 只驗收本機工具；Stage 5 完整獨立審查通過後，才依 Stage 6 授權操作真實環境。
技術選擇見 [技術文件](../tech-stack.md)，工作進度見 [tasks](../../openspec/changes/bootstrap-discord-bot/tasks.md)。
2026-11-05 使用者已確認兩環境部署、測試與 Stage 6 完成；當時未同步的討論與驗收明細已於 2026-11-09 補回。原始完成依據、完整部署版本與人工未測限制均保留於 [驗收紀錄](../../openspec/changes/bootstrap-discord-bot/acceptance.md)。以下部署步驟供日後操作參考，不表示現在需要重做。

## 本機安裝與檢查

使用 Node.js 24，在專案根目錄執行：

```bash
npm ci
npm run typecheck
npm test
npm run build:test
npm run build:production
```

`npm ci` 只安裝 lockfile 中的依賴。後四個指令不需要 Discord／Cloudflare 真實憑證，不會建立遠端資源。
`build:*` 都固定帶 `--dry-run`，輸出至 `dist/test`、`dist/production`，不會部署。
尚未設定真實雲端資源時，打包顯示 `No bindings found` 是預期結果；實際 Worker 設定留到 Stage 6 配置。
測試分為 `workers` 與 `tools`；可用 `npm test -- --project tools` 只驗證操作工具。

## 啟動本機入口

只在檔案不存在時複製範例，保留自己已有的設定：

```bash
cp -n .dev.vars.example .dev.vars
npm run dev
```

範例的金鑰與 ID 全是佔位值。依終端機顯示的網址另開終端機測試，預設是 `http://localhost:8787`：

```bash
curl -i http://localhost:8787/
curl -i http://localhost:8787/interactions
curl -i -X POST http://localhost:8787/interactions -H 'Content-Type: application/json' -d '{"type":1}'
```

預期依序為 404、405、401；POST 的 401 是因為沒有簽章。未複製設定或設定無效時，POST 預期為 503。
有效 PING 需要配對金鑰與已簽署本文；自動測試已提供這個情境。瀏覽器打開首頁不會出現網站。

## 環境與設定各放哪裡

| 用途 | Wrangler 設定 | 本機設定檔 | 本機啟動 |
| --- | --- | --- | --- |
| 本機開發 | 根目錄 `wrangler.jsonc` | 根目錄 `.dev.vars` | `npm run dev` |
| 測試 Bot | `environments/test/wrangler.jsonc` | 同目錄 `.dev.vars` | `npm run dev:test` |
| 正式 Bot | `environments/production/wrangler.jsonc` | 同目錄 `.dev.vars` | `npm run dev:production` |

測試與正式分別命名為 `diary-test`、`diary-production`。名稱仍可在建立真實資源前調整，但必須各自獨立並記錄。
Wrangler 從所選設定檔的目錄讀取 `.dev.vars`；兩組不共用目錄，也不從根目錄或另一組補值。
不要另建共用 `.env` 或設定 `CLOUDFLARE_INCLUDE_PROCESS_ENV=true`，以免本機工具載入額外的全域設定。

| 設定 | 用途 | 放置方式 |
| --- | --- | --- |
| `DISCORD_PUBLIC_KEY` | 驗證該應用程式的 Ed25519 簽章，並非秘密私鑰 | 各組本機 `.dev.vars`／雲端 Worker 設定 |
| `DISCORD_APPLICATION_ID` | 確認請求屬於該應用程式 | 同上；字串形式的數字 ID |
| `DISCORD_OWNER_ID` | 允許的 Discord 帳號 | 同上；不使用暱稱或角色 |
| `DISCORD_GUILD_ID` | 允許的私人伺服器 | 同上；可與另一環境相同 |
| `DISCORD_TEST_*`、`DISCORD_PRODUCTION_*` | 各組註冊用的 `APPLICATION_ID`、`GUILD_ID`、`BOT_TOKEN` | 根目錄 `.env.registration`，只給 Node.js 工具讀取 |
| Cloudflare 部署憑證 | 未來操作 Worker | 操作者的登入環境／秘密管理工具，不放進 repo |

Worker 不需要 Bot token；註冊工具不需要公開金鑰。測試／正式應用程式、公開金鑰及 token 各自獨立，帳號與私人伺服器可以共用。
範例只放佔位值。實際設定檔均已忽略，請勿將真實設定填回 `.example` 檔或提交憑證。
本機 `.dev.vars` 不會自動成為已部署 Worker 的設定，雲端設定須於 Stage 6 另行配置。

## 註冊工具的本機 dry run

```bash
cp -n .env.registration.example .env.registration
npm run register:ping -- --env test --dry-run
npm run register:ping -- --env production --dry-run
```

範例值足以執行 dry run。輸出只包含環境、應用程式 ID、伺服器 ID、指令名稱與 `dryRun: true`，不包含 token，也不發 HTTP 請求。
`--env` 必填，只接受 `test` 或 `production`；缺值、未知參數或設定錯誤會以非零狀態停止，不預設正式環境。
只讀取選定環境的前綴，不回退到通用 `DISCORD_BOT_TOKEN` 或另一個環境；兩組同時設定時，也拒絕共用應用程式 ID 或 token。

先確認這裡顯示的應用程式／伺服器與對應 Worker 一致。真實註冊才移除 `--dry-run`，這屬於後面的 Stage 6 操作。
工具只 POST 單一 guild command；Discord 會建立或更新同名 `/ping`，不註冊全域指令、不整批覆寫其他指令，也不在 Worker 啟動時執行。
HTTP 失敗只顯示狀態碼，網路錯誤只顯示通用訊息，不輸出 Discord 回傳本文、token 或例外堆疊；失敗後先確認設定再人工重試。

## Stage 6：接上真實測試環境

以下操作會改動外部服務。前置條件是 Stage 5 通過，且已有對應測試環境授權；Stage 4 不執行。

1. 核對當時 Cloudflare 免費額度與帳號限制，不升級付費、不建立 D1、自訂網域或自動部署。先記錄版本、兩組應用程式 ID、伺服器與 Worker 名稱；不要記錄 token。
2. 在 Discord Developer Portal 建立兩組獨立應用程式，分別取得各自的 Application ID、Public Key 與 Bot token。只安裝到自己的私人伺服器，授權 `applications.commands`；本次無需 Administrator、Message Content intent 或讀取歷史訊息權限。純指令不要求額外的 `bot` 安裝 scope；之後日記頻道發送另行規劃。
3. 複製兩組 `environments/*/.dev.vars.example` 為同目錄 `.dev.vars`，填入對應真實設定；將兩組註冊設定填入 `.env.registration`。註冊用 Application ID／Guild ID 必須與對應 Worker 一致，兩組 token 不得共用。
4. 先跑測試註冊 dry run 並核對目標，再安裝測試應用程式到指定伺服器，設定測試 Worker。以下命令只選測試設定：

```bash
npm run register:ping -- --env test --dry-run
npx wrangler secret bulk environments/test/.dev.vars --config environments/test/wrangler.jsonc
npx wrangler deploy --config environments/test/wrangler.jsonc
npm run register:ping -- --env test
```

這裡用 `secret bulk` 保存四個 Worker 設定，其中公開金鑰與 ID 雖非 token，也不需寫回版本控制。
首次若工具要求建立 Worker，確認名稱只限已核對的 `diary-test`；不要接受其他目標或付費升級。
複製的範例只有四個 Worker 設定，禁止在這個檔案加入 Bot token。

5. 在測試應用程式設定 Interactions Endpoint URL 為部署後的 `https://…workers.dev/interactions`，確認 Discord 驗證入口成功。對該網址發沒有簽章的 POST，應回 401；若回 503，先補齊 Worker 設定。
6. 在手機、電腦與指定伺服器的另一個文字頻道分別執行測試 `/ping`，確認 3 秒內收到私人 `Pong!`。可用第二帳號時，再確認拒絕提示也只有該帳號看見；沒有第二帳號則記錄此人工項目未執行，引用自動測試，不當成人工驗收通過。
7. 確認沒有公開回覆、私訊指令或對正式設定的改動，記錄實際版本、時間與結果。失敗先修復測試環境，保留正式環境。

## Stage 6：正式環境與回復

測試通過且正式操作已有授權後，另行核對正式目標，重做前述步驟。命令必須明確選正式環境：

```bash
npm run register:ping -- --env production --dry-run
npx wrangler secret bulk environments/production/.dev.vars --config environments/production/wrangler.jsonc
npx wrangler deploy --config environments/production/wrangler.jsonc
npm run register:ping -- --env production
```

設定正式應用程式的入口並重做手機、電腦、頻道與無簽章請求驗收；測試環境仍應獨立可用。

如果已部署版本有問題：

- 有上一個可用版本時，先確認版本 ID，再以 `npx wrangler rollback "PREVIOUS_VERSION_ID" --config environments/test/wrangler.jsonc` 回復指定環境；正式環境要改用正式設定檔。`PREVIOUS_VERSION_ID` 須換成已記錄的可用版本。
- 首次部署沒有可回復版本時，清除該 Discord 應用程式的 Interactions Endpoint URL，並停用其 `/ping`：先以 Discord 的 Get Guild Application Commands 查出 `name=ping`、`type=1` 的 command ID，再以 Delete Guild Application Command 刪除該單一指令。不要整批覆寫其他指令或改到另一個應用程式。
- 回復 Worker 程式不會一併回復 Discord 入口、指令或憑證設定。操作前保存非秘密的原設定，操作後分別確認；記錄版本、時間、預期／實際結果與未驗證項目，不記錄 token 或完整互動本文。

## 規格情境與驗收位置

| 規格情境 | 自動測試／未來人工驗收 |
| --- | --- |
| 有效簽章 | `tests/interactions.test.ts` 的 signed protocol PING |
| 缺少或錯誤簽章 | 同檔 missing／forged／malformed signature |
| 本文或時間戳記被修改 | 同檔 body／timestamp changed after signing |
| 入口驗證不含使用者資訊 | 同檔 PING without user or guild fields |
| 偽造入口驗證 | 同檔 forged signature；回 401、不回 PONG |
| 擁有者在兩個文字頻道使用 | `tests/commands.test.ts` 的兩個 channel 案例；真實驗收完成依據與明細限制見驗收紀錄 |
| 其他使用者包含管理員 | 同檔 privately denies 的 another user／administrator |
| 擁有者在錯誤伺服器或私訊使用 | 同檔 another guild／DM from the owner |
| 無法核對操作者 | 同檔 missing member／user／ID 等拒絕案例 |
| 正常連通 | 同檔私人 Pong 格式；真實手機、電腦、3 秒與可見性驗收的完成依據與明細限制見驗收紀錄 |
| 未支援的指令 | 同檔 unknown command 與同名 context-menu command |
| 已簽署的錯誤內容 | 入口測試 signed invalid input 與指令測試 malformed command data |
| 缺少必要設定 | 入口測試 missing／invalid settings；回 503 |
| 無雲端憑證的本機驗收 | 三組工具檢查：Workers 測試、Node 註冊／環境測試及兩組打包 dry run |
| 明確選擇測試環境 | `tests/tooling/register-ping.test.ts` 與 `environments.test.ts`；真實環境驗收完成依據與明細限制見驗收紀錄 |
| 註冊操作未指定環境 | 註冊測試 requires exactly one supported environment；不發 HTTP |

測試通過不等於已部署；所有真實結果仍須按 tasks 記錄後才勾選 Stage 6。

## 官方參考

- [Discord 指令授權與單一 guild command API](https://docs.discord.com/developers/interactions/application-commands)
- [Cloudflare 本機設定檔載入規則](https://developers.cloudflare.com/workers/local-development/environment-variables/)
- [Cloudflare 免費額度與限制](https://developers.cloudflare.com/workers/platform/limits/)
- [Cloudflare 回復版本](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/)
