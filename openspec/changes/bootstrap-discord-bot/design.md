# Design

## Context

動機與範圍見 [proposal.md](proposal.md)，外部行為以 [能力規格](specs/discord-command-access/spec.md) 為準。
`main` 已移除舊程式與套件設定，目前沒有可沿用的 v2 執行入口或測試工具；不從 `v1` 搬回舊框架。
全專案技術選擇與原因見 [技術文件](../../../docs/tech-stack.md)。

本設計處理新後端、Discord 外部整合與安全驗證，因此需要設計文件。
使用者已確認私人伺服器、擁有者與伺服器雙重限制、`/ping` 不綁定單一文字頻道、
指令回覆僅本人可見，以及測試／正式環境分離。以下是實現這些行為的工程安排。

## Goals / Non-Goals

**Goals:**

- 用一個 HTTP 入口完成驗證、授權、指令回覆，讓後續功能有共同入口。
- 在接近正式的 Workers 執行環境測試，特別驗證簽章、原始本文與回覆格式。
- 不靠真實憑證就能做本機自動驗收；真實連線另有清楚的人工驗收步驟。

**Non-Goals:**

- 不建立資料存取層、資料表、背景工作、通用 Agent 架構或網站。
- 不做登入系統、多人角色管理、完整防重播儲存機制或流量壓力測試。
- 不建立自動部署、公開本機通道或付費備援服務。

## Decisions

### 一個 HTTP 入口與小型處理流程

以 Hono 提供 `POST /interactions`，由 Workers 的 `fetch` 入口接收請求。
依序處理：必要設定 → 原始本文與簽章 → 解析與結構檢查 → 協定 `PING` 或指令授權 → 指令回覆。
其他路徑回 HTTP 404；`/interactions` 的其他方法回 HTTP 405。

將 Discord 驗證、授權判斷與指令處理保持可分開測試的邊界，路由只負責串接。
目前不建立額外服務、依賴注入容器或抽象資料庫介面；這些都不是 `/ping` 所需。
相較常駐 Gateway Client，HTTP 可以配合既定 Workers 方式，不需要保持連線。
相較把所有判斷寫在路由內，分開處理較容易測出驗證順序錯誤，也方便後續加入指令。

### 先驗證原始本文，再讀取互動內容

採 Discord 維護的 `discord-interactions` 之 `verifyKey`，以時間戳記及原始本文驗證 Ed25519 簽章。
Hono 先保留原始本文，驗證後才解析 JSON；不能先解析再重新序列化，否則空白或編碼差異會破壞簽章。
不使用 Express 專用 middleware，也不自行實作密碼學。

在實際 Workers 測試執行環境確認所選版本的相容性，並鎖定相容依賴版本。
畸形簽章造成的驗證例外按無效簽章處理，不變成未處理的 HTTP 500。
時間戳記必須參與簽章驗證；本次不額外承諾某個時間差門檻或防重播能力。
`/ping` 沒有寫入副作用；未來有寫入的 change 應另行決定重複請求與防重播策略。

### 協定驗證與指令授權分開

簽章有效且應用程式 ID 相符的協定 `PING`，直接回 `{"type":1}`。
它不需要使用者或伺服器資料，否則 Discord 設定 Interactions Endpoint 時會被擋住。

應用程式指令另外核對 `guild_id` 與 `member.user.id`；必須與設定中的伺服器和擁有者 ID 同時相符。
不從使用者輸入、顯示名稱或角色推算身分；私訊與缺少身分的指令都拒絕。
Discord 的指令可見性設定只是操作輔助，後端每次都核對，避免只靠私人伺服器或管理員權限。

### 直接回覆，統一私人訊息

`/ping` 直接在原 HTTP 回應中回覆類型 4、`Pong!` 與 `flags: 64`（`EPHEMERAL`）。
拒絕指令回「無法使用此指令」；通過授權但尚未支援的指令回「不支援此指令」。
這些回覆都只讓操作者看見，不公布允許的帳號或伺服器 ID。

不查外部服務、不發額外頻道訊息，也不使用延後回覆與背景工作，減少超過 3 秒初次回覆期限的風險。
這只決定本 change 的指令回覆；不把未來日記內容也預設成無法滑動閱讀的私人回覆。

| 情況 | HTTP 與回覆 |
| --- | --- |
| 必要環境設定缺少或格式錯誤 | 503，通用錯誤，不處理互動 |
| 設定完整，但必要簽章標頭缺少或驗證失敗 | 401，不產生 Discord 成功訊息 |
| 簽章有效，但 JSON、必要結構、應用程式 ID 或互動類型不符 | 400，不執行指令 |
| 有效協定 `PING` | 200，類型 1，不要求使用者與伺服器 |
| 可辨識的指令未通過帳號／伺服器限制 | 200，類型 4，私人拒絕訊息 |
| 擁有者在指定伺服器執行 `/ping` | 200，類型 4，私人 `Pong!` |
| 擁有者在指定伺服器執行未知指令 | 200，類型 4，私人未支援提示 |

應用程式指令需有對應應用程式 ID、互動類型與可辨識的指令資料；
缺少操作者／伺服器屬於授權拒絕，其他無法辨識的結構屬於 400。
非預期內部錯誤只回通用 500，不把例外堆疊或設定值送到回應與應用程式日誌。

### 設定與憑證各有用途

| 設定 | 用途 | 放置方式 |
| --- | --- | --- |
| `DISCORD_PUBLIC_KEY` | 驗證該應用程式的請求，不是秘密金鑰 | 對應環境的 Worker 設定；本機使用測試用值 |
| `DISCORD_APPLICATION_ID` | 核對收到的應用程式與註冊目標 | 對應環境的設定 |
| `DISCORD_OWNER_ID` | 允許的操作者 | 對應環境的設定 |
| `DISCORD_GUILD_ID` | 允許的私人伺服器 | 對應環境的設定 |
| `DISCORD_BOT_TOKEN` | 執行指令註冊工具 | 各環境獨立的本機秘密或秘密管理工具，不放到執行 `/ping` 的 Worker |
| Cloudflare 部署憑證 | 未來手動操作指定 Worker | 操作者環境，不進 repo 或 Bot 執行環境 |

ID 保持字串，檢查為非空十進位 ID，不轉為可能失去精度的 JavaScript number。
公開金鑰檢查為 Ed25519 公開金鑰的十六進位格式；必要設定不完整就停止處理。
本機秘密檔採 `.dev.vars`，提供不含真實值的範例並加入忽略規則。
測試與正式設定分開，禁止缺少值時自動沿用另一個環境。
即使 ID 不是 token，repo 範例仍使用佔位值，避免不必要公開私人設定。

### 測試與正式環境分離，但不增加常駐服務

測試及正式各有一個 Discord 應用程式與一個獨立 Worker；各自保存公開金鑰、應用程式 ID 與 token。
兩組可安裝在同一個私人伺服器；帳號 ID／伺服器 ID 可以相同，應用程式、Worker、入口網址與 token 必須不同。
使用名稱區分兩個 Bot，驗收時明確選擇要測試的應用程式。

先用 Wrangler 本機開發與自動測試。Discord 真實連線採未來測試 Worker 的 HTTPS 入口，
不以本機測試通過代替真實連線驗收，也不要求先架公開本機通道或購買網域。
兩組 Worker 使用免費方案限制，不自動升級；免費額度屬帳號限制，不能假設拆兩個 Worker 就得到兩份額度。

### 指令註冊是獨立的人工作業

未來提供一次性 TypeScript 註冊工具，以 Discord REST API 在明確選定的應用程式及伺服器註冊 `/ping`。
環境參數必填，只允許測試或正式；沒有參數、缺設定就停止，不能預設正式環境。
提供不發 HTTP 請求的 dry run，顯示目標環境、應用程式與伺服器，永不輸出 token。
以單一 guild command 的建立／更新介面處理 `/ping`，不做全域註冊或整批覆寫其他指令。

相較啟動 Worker 時自動註冊，獨立工具較容易檢查環境與失敗，也不必把 Bot token 放進 Worker。
目前只需 slash command 安裝所需範圍，不要求 Administrator、Message Content intent 或讀取歷史訊息權限。
未來日記要另發頻道訊息時，再由對應 change 增加必要權限。

### 自動驗收與人工驗收各自負責不同證據

本機採 Vitest 與 Cloudflare 官方 Workers 測試整合；使用當時相容的官方套件與版本並鎖定依賴。
透過實際 Worker HTTP 入口測試簽章、驗證順序、授權與回覆；使用獨立測試用 Ed25519 金鑰簽署實際本文，
不可把驗證器整個 mock 成成功。註冊工具則攔截 HTTP，驗證目標與秘密不外洩，禁止真實註冊。

每張票先看到測試因缺少預期行為而失敗，再寫最小實作、通過後重構。
測試需涵蓋原始本文的空白、繁體中文、修改時間戳記、其他使用者／伺服器、缺少身分、
未知指令、設定錯誤與測試／正式隔離，不只測正常路徑。
本機測試不對網際網路延遲做保證；3 秒期限另以未來手機與電腦上的真實指令驗收確認。

目前 repo 仍要求 Markdown ticket 與每票新 session 審查。
實作前將 [tasks.md](tasks.md) 的三組工作登記為三張 `.scratch/diary-v2/issues/` 實作票，引用本 change 規格；
本次不建立票或修改工作流程。一次只實作一票，該票獨立審查通過才接下一票。
舊草稿不作為覆蓋本次已確認需求的依據；若未來需要整併，另處理，不在此 change 自動搬移全部歷史文件。

## Risks / Trade-offs

- 原始本文在驗證前被修改 → 由真實簽章整合測試涵蓋空白、繁體中文與竄改案例。
- 限制使用者時誤擋 Discord 協定驗證 → 先驗證簽章，再區分協定與指令，分別驗收。
- 兩個 Bot 容易選錯 → 清楚命名，註冊必填環境，dry run 核對目標；正式操作不依賴預設值。
- 本機通過但雲端環境缺設定或逾時 → typecheck、Workers 執行環境測試、打包檢查之外，另保留真實連線驗收。
- 錯誤日誌洩漏互動 token 或未來私人輸入 → 不記完整本文、憑證或堆疊，只記通用原因碼與必要狀態。
- 私人回覆無法作為長期日記瀏覽紀錄 → 本次只用於連通與拒絕提示，日記頻道行為另寫規格。
- 免費方案額度或政策改變 → 未來部署前核對當時限制，超過限制就停止並回報，不自動升級。
- 目前未做防重播與持久化 → 不宣稱完整寫入安全；寫入功能需另外設計重複提交處理。

## Migration Plan

沒有舊版資料或資料庫遷移。本次只產出規劃，下列是未來實作後的驗收安排，不代表現在已獲部署授權。

1. 安裝鎖定的依賴後，在沒有真實雲端憑證的環境跑 typecheck、自動測試及 Wrangler 打包 dry run；不得建立遠端資源。
2. 三張實作票逐票完成 TDD 與新 session 獨立審查，留下測試與修正紀錄。
3. 未來獲准雲端操作後，先建立／確認測試應用程式與測試 Worker，核對免費方案與設定，不建立 D1。
4. 先 dry run 確認註冊目標，再只註冊測試 `/ping`。將測試應用程式的 Interactions Endpoint 指向測試 Worker；確認 Discord 入口驗證通過，無簽章 HTTP 請求仍回 401。
5. 在手機與電腦各執行 `/ping`，確認初次回覆在期限內且只有操作者可見；在另一個文字頻道再驗證一次。若有第二帳號可用，確認拒絕訊息只對該帳號可見；沒有就以自動測試覆蓋後端拒絕，不假稱人工驗收完成。
6. 確認測試入口、註冊與 token 沒有改到正式設定；另經正式操作授權後，對正式應用程式與 Worker 重複設定及驗收。
7. 記錄環境、版本、時間、預期／實際結果與人工未驗證項目，不記 token 或完整互動本文；未執行的雲端驗收保持待辦，不把本機通過寫成已上線。

若測試失敗，保留正式環境，修正後再驗收。正式環境若有上一個可用版本則回復該版本；
首次部署若無可回復版本，移除該應用程式的入口設定並停用其 `/ping`，停止提供功能。
回復程式不等於回復 Discord 設定，操作紀錄需同時保存非秘密的入口與指令設定。

## Open Questions

- 實際應用程式 ID、帳號／伺服器 ID、Worker 名稱與入口網址，在未來建立環境時填入。
- 雲端驗收時間，以及是否有第二帳號可人工驗證拒絕提示，待實際驗收時安排；後端拒絕情境已納入自動測試，不依賴此安排。

## References

- [Hono 的 Workers 入口與本機開發](https://hono.dev/docs/getting-started/cloudflare-workers)
- [Discord 入口驗證與安全標頭](https://docs.discord.com/developers/interactions/overview)
- [Discord 回覆類型、私人訊息與 3 秒期限](https://docs.discord.com/developers/interactions/receiving-and-responding)
- [Discord guild command 與註冊介面](https://docs.discord.com/developers/interactions/application-commands)
- [Discord 官方簽章驗證輔助套件](https://github.com/discord/discord-interactions-js)
- [Cloudflare Workers 的 Vitest 整合](https://developers.cloudflare.com/workers/testing/vitest-integration/)
- [Cloudflare 本機設定與秘密](https://developers.cloudflare.com/workers/local-development/environment-variables/)
- [Cloudflare Workers 免費方案限制](https://developers.cloudflare.com/workers/platform/limits/)
