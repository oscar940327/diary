# Stage 5 獨立審查紀錄

日期：2026-11-03。本 session 在 Stage 1–4 提交完成後，依專案 `code-review` skill，平行交由兩個獨立代理審查 Standards 與 Spec；主代理整合驗證與紀錄。本次只執行 Stage 5。

## Scope

- 分支：`change/bootstrap-discord-bot`。
- 固定起點：`116c9d8ebfb22829fe7b96891b244dc5d763d71d`。
- 受審 HEAD：`acfefce1430c02b44e5b095c13658c972e33f4e5`。
- 比較命令：`git diff 116c9d8...acfefce1430c02b44e5b095c13658c972e33f4e5`，等同啟動時的 `git diff 116c9d8...HEAD`；共 48 個檔案。
- 提交清單：`acfefce`、`ad76973`、`a5bfa8b`、`cddebae`、`186ceef`、`a4c4f61`，由 `git log 116c9d8..HEAD --oneline` 取得。
- 工作區原有 `DISCUSSION.md` 與 `docs/discussions/2026-11-part-02.md` 修改予以保留，不算入固定受審差異。歷史 ADR 刪除已有使用者授權。

## Standards

獨立代理 `standards_review`：未發現需要修正的規範違反或具體 code smell；硬性違反 0 項、判斷型 finding 0 項，無阻擋問題。

依 `AGENTS.md`、`docs/agents/development-workflow.md`、領域與工作追蹤文件、`CONTEXT.md`、技術文件、討論紀錄規則及 README 核對，並套用 skill 的完整 Fowler smell baseline。現行 repo 規則優先；工具已強制的事項交由檢查驗證。

- 實作維持 TypeScript／Hono／Workers 的小型入口、驗證、授權與指令邊界；沒有引入舊框架、額外 tickets／ADR、日記、Agent 或資料庫功能。
- 已檢查 `src/`、註冊工具、四份測試、fixture、依賴與設定；命名與私人訊息集中處理合理，未發現值得回報的重複分支、過早抽象或多餘委派。
- 範例只有假值，秘密檔已忽略；Worker 與註冊工具的憑證用途分開，錯誤只輸出通用訊息。操作文件區分本機證據與未執行的 Stage 6。
- 歷史 ADR 清理已授權且說明已同步；討論摘要與分冊符合長度規則。

本軸另執行 typecheck 與固定差異的 `git diff --check`，均通過，未修改檔案。

## Spec

獨立代理 `spec_review`：未發現可修正的規格缺漏、範圍擴張或錯誤實作；0 項 findings，無阻擋問題。

核對本 change 的 proposal、[能力規格](specs/discord-command-access/spec.md)、design、tasks，以及現行技術決策。

| 規格情境／串接範圍 | 審查結果與證據 |
| --- | --- |
| 有效／缺少／錯誤簽章，本文或時間戳記竄改 | `src/discord.ts` 先檢查設定，再以原始位元組及時間戳記呼叫官方 `verifyKey`；畸形標頭或驗證失敗回 401。`tests/interactions.test.ts` 涵蓋配對／錯誤金鑰、空白與繁中保真及竄改。 |
| 協定 PING／偽造 PING | 簽章與應用程式 ID 通過後，先回 PONG，再進指令授權；不要求使用者或伺服器。偽造簽章回 401。 |
| 擁有者兩個頻道、其他使用者含管理員、錯誤伺服器／私訊、缺少身分及偽造輸入 | 只核對已簽署 `guild_id` 與 `member.user.id`，不限制頻道，不從參數、角色或頂層 user 放行；`tests/commands.test.ts` 有成功及拒絕案例。 |
| 正常連通、未知指令與私人旗標 | 成功、拒絕與未知指令均直接回 HTTP 200、類型 4、flags 64；未知指令不誤回 Pong。測試確認不呼叫外部服務、不洩漏私人輸入。 |
| 無效內容、設定缺漏及錯誤順序 | 簽章通過才解析；無效 JSON／結構／應用程式／互動類型回 400，缺少或無效設定回 503。`src/index.ts` 的 404／405 與通用 500 也有回歸測試。 |
| 無真實憑證的本機驗收 | 測試產生專用 Ed25519 金鑰；註冊 HTTP 被攔截，Worker 無 Bot token 需求，也沒有資料保存或背景工作。 |
| 明確選環境及缺少環境時停止 | `scripts/register-ping.ts` 必填 test／production，dry run 不發 HTTP，設定不跨環境回退；工具測試核對目標與錯誤。 |
| 環境隔離、單一指令註冊及秘密 | 兩個 Worker 目錄與名稱獨立；Wrangler 測試確認不載入根目錄／另一組設定。只 POST 指定 guild 的單一 ping，不整批覆寫；失敗不輸出 token、回應本文或堆疊。 |
| 安裝權限、操作文件及回復 | 文件只要求 applications.commands，不要求管理員、Message Content 或歷史訊息權限；提供兩組 dry run、部署及回復步驟，明示真實驗收尚未執行。 |

外部介面另核對 [Discord 官方指令文件](https://docs.discord.com/developers/interactions/application-commands)：`applications.commands` 可獨立安裝，Bot token 可註冊 guild command，同名單一 POST 為建立／更新。鎖定版本 Wrangler 原始碼也確認 `secret bulk` 支援 dotenv 輸入。此核對未操作雲端。

## Verification

最終使用 Node.js `v24.22.2`，依 README 要求執行：

- `npm run typecheck`：通過。
- `npm test`：4 個檔案、118 個測試全部通過。
- `npm run build:test`、`npm run build:production`：均通過，只執行打包 dry run，產物各為 81.21 KiB；未配置雲端 bindings 的提示符合目前狀態。
- `openspec validate bootstrap-discord-bot --strict`：通過。
- `git diff --check 116c9d8...acfefce` 與本次工作區差異檢查：通過。

首次預設沙箱執行測試因禁止 localhost 監聽而中止，不能算測試通過；取得本機執行權限後完整重跑成功。Wrangler 日誌改放 `/private/tmp`，避免寫入沙箱外的使用者設定目錄。預設 Node 22 的先行檢查不代替上述 Node 24 最終結果。

## Resolution

Standards 0 項、Spec 0 項，各軸均無最高嚴重度問題。沒有阻擋問題，因此沒有修改產品程式，也沒有為此新增回歸測試；既有完整回歸驗證通過。兩個獨立報告與本機證據核對後，Stage 5 審查通過，tasks 5.1–5.3 可勾選，整體為 16/21。

本次到此停止。Stage 6 的 5 項 tasks 全部保留未勾選；未部署、未真實註冊指令，手機／電腦、3 秒期限、真實私人可見性及雲端隔離尚未驗收，不宣稱已上線。

## 2026-11-05 合併前複查

使用者已確認兩環境部署、測試及整個 Stage 6 完成，原始紀錄日後補回；其完成依據與限制見 [驗收紀錄](acceptance.md)。上方 Stage 5 結語保留為 11 月 3 日的歷史狀態。

固定差異為 `git diff 116c9d8ebfb22829fe7b96891b244dc5d763d71d...a13140476a38a50ca3e66455bfe6611ea174f836`，共 50 個檔案；提交為 `a131404`、`0f76274`、`acfefce`、`ad76973`、`a5bfa8b`、`cddebae`、`186ceef`、`a4c4f61`。產品程式自 `acfefce` 之後未變更。本輪以 skill 要求的兩個獨立代理做合併前複查，不取代先前已完成的新 session Stage 5。

### Standards

獨立代理 `standards_review`：0 項 findings。核對入口、Discord 驗證與授權、註冊工具、測試及環境設定，未發現違反現行 repo 規則或需要修正的實質程式問題。路由與處理分工清楚，ID 保持字串，私人回覆集中處理；沒有需要追加抽象或重構的 baseline smell。

### Spec

獨立代理 `spec_review`：0 項 findings。HTTP 入口、原始本文驗證、應用程式核對、協定 PING、雙重授權、私人回覆、單一 guild 註冊與環境隔離符合能力規格，未發現缺漏、錯誤實作或範圍擴張。操作文件過時的驗收待辦描述已在本輪收尾更新。

### Verification

- Node.js `v24.13.1`：`npm run typecheck` 通過，`npm test` 為 4 個檔案、118 個測試全部通過。
- `npm run build:test`、`npm run build:production` 均通過；各 81.21 KiB，固定 dry run，未部署。未配置本機雲端 bindings 的提示不代表遠端環境缺少設定。
- 首次測試及打包受沙箱禁止存取父目錄／Wrangler registry 影響；取得所需本機執行權限後重跑成功，未把失敗那次視為通過。
- 本次無需修改產品程式，也未新增測試；部署與人工測試依使用者確認，本次沒有重新驗證雲端。

Standards 0 項、Spec 0 項，兩軸均無阻擋問題或最高嚴重度問題；可進行 PR 合併準備。
