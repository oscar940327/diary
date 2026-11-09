# Stage 6 部署與驗收紀錄

更新日期：2026-11-09（補回原 2026-11-04 的明細）。Stage 1–6 已完成，21/21；PR #2 於台灣時間 11 月 6 日合併，change 尚未歸檔。

## 本次補記來源與範圍

- 11 月 5 日在另一台電腦依使用者確認結案，當時缺少的部署明細及紀錄限制原文保留於下方「11 月 5 日結案紀錄」。
- 11 月 9 日從本機提交 `10ca1ad` 補回兩環境入口、完整版本、原始人工回報及回復步驟；兩邊確認的是同一個已完成 change，沒有重做功能或改寫過去的確認依據。
- 下方 11 月 4 日明細是原有紀錄的恢復，不代表本次重新查詢遠端版本、重跑 Discord 驗收或執行 rollback；當日完整版本的日誌來源與人工未測項目均保留。
- 合併前複查及原始 118 個測試證據見 [review.md](review.md)。本次僅處理文件同步，未重註冊指令、重新部署或存入憑證。

## 2026-11-04 部署驗收明細（2026-11-09 補回）

### 前置與目標

- Stage 5 已通過，產品實作版本為 `acfefce1430c02b44e5b095c13658c972e33f4e5`，見 [審查紀錄](review.md)。
- 首輪使用者只授權測試環境，後續確認維持雙環境並接續正式部署與收尾；帳號與外部安裝、註冊、部署由使用者親自操作，Agent 提供步驟、本機檢查與無簽章 HTTP 驗證，沒有控制瀏覽器代為部署。
- 首次縮小 scopes 後的登入要求被自動核准審查拒絕；使用者明確同意帳號資訊讀取、Worker 程式修改與執行紀錄讀取權限後，重新登入成功，`wrangler whoami` 已確認帳號及 scopes（`account:read`、`user:read`、`workers_scripts:write`、`workers_tail:read`、`offline_access`）。未取得其他服務的寫入權限。
- 已填寫且受 Git 忽略的本機設定已完成格式與一致性檢查，未輸出 token。首輪 6.1–6.3 僅操作測試；後續使用者已部署正式 Worker，正式註冊與驗收進度另記於下方 6.4。

| 項目 | 測試目標 | 正式目標 |
| --- | --- | --- |
| Cloudflare 帳號／實際方案 | 已建立並確認單一登入帳號；2026-11-04 使用者從方案頁確認為 Workers Free | 同一帳號，兩個 Worker 共用免費額度 |
| Worker 名稱 | `diary-test`，使用者已部署並提供網址；HTTP 簽章拒絕行為已實測 | `diary-production`，使用者已部署；設定目錄、Worker 名稱與測試各自獨立 |
| Discord 應用程式 | `.env.registration` 的 `DISCORD_TEST_APPLICATION_ID`，與測試 Worker 設定一致 | `DISCORD_PRODUCTION_APPLICATION_ID` 與測試不同；使用者確認正式安裝、guild `/ping` 註冊與 Discord 入口驗證成功 |
| 擁有者／私人伺服器 | ID 格式與設定一致性通過，擁有者手機／電腦實測通過 | 正式 ID 與註冊設定一致，使用者回報擁有者手機／電腦實測通過 |
| 入口網址／部署版本／指令 ID | `https://diary-test.oscar940327.workers.dev/interactions`；完整版本見下方 6.5；guild `/ping` 已註冊，指令 ID 未查詢 | `https://diary-production.oscar940327.workers.dev/interactions`；完整版本見下方 6.5；正式 `/ping` 註冊及入口驗證成功，指令 ID 未查詢 |

### 免費限制與操作邊界（6.1，已核對）

- 2026-11-04 再次核對官方文件：Workers Free 每帳號每日 100,000 次請求，UTC 午夜重設；HTTP 請求 CPU 時間上限 10 ms，網路等待不算 CPU 時間。使用者已從方案頁確認實際帳號為 Workers Free；兩個 Worker 共用帳號額度，沒有取得兩份額度。未讀取帳號當日用量，不宣稱尚餘特定次數。
- 兩組皆使用免費方案及 `workers.dev` 網址，不新增 D1、付費方案、自訂網域或自動部署。
- 兩份 Wrangler 設定使用不同名稱及獨立設定目錄，沒有 D1、網域路由或付費服務設定；兩個 Discord 應用程式 ID 已在本機核對不同。6.1 核對時尚未配置正式 token，後續 6.4 本機準備已確認正式 token 與測試不同，不互相沿用。
- 來源：[Workers 限制](https://developers.cloudflare.com/workers/platform/limits/)、[Workers 計價](https://developers.cloudflare.com/workers/platform/pricing/)。

### 實際結果

| task | 驗收 | 狀態 |
| --- | --- | --- |
| 6.1 | 真實帳號方案、目標及兩組應用程式隔離核對 | 通過：使用者確認 Workers Free、官方額度已查核；兩個應用程式 ID 不同，Worker 目標名稱與設定目錄獨立，目標清單及禁止新增項目見上方。遠端 Worker 部署屬後續 tasks |
| 6.2 | 測試應用程式安裝至指定伺服器 | 使用者回覆安裝完成，後續已回報手機／電腦在兩個頻道執行測試 `/ping` 成功 |
| 6.2 | 真實目標註冊 dry run、測試部署與單一 guild `/ping` 註冊 | 通過：測試註冊 dry run 已核對；使用者回報部署網址及版本前綴，HTTP 入口可連線，並確認 `npm run register:ping -- --env test` 註冊成功 |
| 6.2 | Discord 入口驗證、無簽章 POST 回 401、正式設定未變 | 通過：2026-11-04 無簽章 JSON `{"type":1}` 實測 HTTP 401、本文 `Invalid request signature`；使用者依 `Diary Test` 的入口設定步驟回報儲存驗證成功。本輪命令與入口均限定測試，沒有執行正式註冊、入口設定或部署 |
| 6.3 | 手機、電腦及另一文字頻道皆於 3 秒內收到私人 `Pong!` | 使用者確認四次皆通過，只有操作者可見且沒有公開回覆 |
| 6.3 | 無私訊指令 | 通過：使用者釐清先前是在伺服器內有鎖頭的私人文字頻道看到 `Diary Test` 的 `/ping`，並確認真正的一對一私訊沒有此指令；私人文字頻道仍屬伺服器，符合不限定單一文字頻道的規格 |
| 6.3 | 第二帳號私人拒絕 | 使用者確認沒有第二帳號，人工未執行；後端拒絕由 `tests/commands.test.ts` 的 `privately denies ...` 案例覆蓋，含其他使用者、管理員、錯誤伺服器與私訊，斷言私人旗標 64 及不洩漏允許 ID；既有 Stage 5 的 118 個測試已通過，見 `review.md` |

### 本次停留位置與接續方式

- Cloudflare 帳號建立及 Wrangler 登入已完成；使用者於 2026-11-04 確認兩份測試設定已填好。
- 本機檢查通過：公開金鑰為 64 位十六進位、三個 Worker ID 為有效格式、兩檔 Application ID 與 Guild ID 分別一致，Worker 設定不含 Bot token；兩個秘密檔均受 Git 忽略。
- 註冊工具 dry run 回傳 `environment: test`、`command: ping`、`dryRun: true`，未發出 Discord HTTP 請求；此證據只代表本機設定可用，不代表憑證有效或已上線。
- 使用者完成儲存後，已讀到格式有效的正式 Application ID，與測試不同；原有測試 Application ID／Guild ID 仍與 Worker 設定相符，加入正式 ID 後再次執行測試註冊 dry run 通過。
- 使用者已回覆 `Diary Test` 安裝完成。使用 Node.js 24 再跑 `npm run build:test` 通過，Wrangler 明確以 `--dry-run` 結束，沒有上傳程式或設定。
- 使用者已提供測試 Worker 網址與版本前綴 `157df2c9`；無簽章 HTTP POST 已由 Agent 實測回 401，未發送憑證或修改遠端設定。
- 使用者已回覆測試指令註冊及 Discord 入口儲存驗證成功，6.2 已完成；這項人工操作結果由使用者回報，Agent 沒有控制瀏覽器或代為註冊。
- 6.3 的四次手機／電腦及兩頻道私人回覆已由使用者確認通過；沒有第二帳號，已記錄人工未執行與對應自動測試證據。
- 使用者已釐清看到指令的位置是伺服器內私人文字頻道，真正的私訊沒有測試 `/ping`；未發現需修正的程式缺陷，因此沒有修改程式、重註冊、刪除指令或新增診斷程式。
- 6.3 完成時，首輪依指定範圍停在測試環境。第二帳號人工拒絕檢查依 task 約定保留未執行及既有自動測試證據；測試部署完整版本 ID 仍僅記前綴 `157df2c9`，尚未補齊，不宣稱已完成 6.5 的整體證據與回復核對。後續正式進度見下方 6.4。

操作方式見 [操作文件](../../../docs/operations/discord-bot.md)。這次可提交的是進度與驗收文件，未包含產品程式變更或雲端憑證。

### 後續 6.4 正式環境部署進度

- 重新評估後，使用者確認維持原規格的雙環境方向，接續原本的正式部署與收尾順序；外部安裝、設定及部署仍由使用者親自操作，Agent 提供步驟與驗證。不採先前討論的單環境改案。
- 使用者完成儲存後，`.env.registration` 的正式 Application ID／Guild ID／Bot token 三欄齊備且格式有效；正式與測試的 Application ID 及 token 均不同，`--env production --dry-run` 通過，沒有呼叫 Discord，也未輸出 token。
- 使用者已填寫正式 Public Key；`environments/production/.dev.vars` 的公開金鑰與三個 ID 格式通過，Application ID／Guild ID 與正式註冊設定一致，公開金鑰及 Application ID 與測試不同，Worker 不含 Bot token。秘密檔受 Git 忽略、權限 600。
- 正式註冊 dry run 及 `npm run build:production` 均通過，Wrangler 明確以 `--dry-run` 結束；使用者已回報 `Diary Production` 依 Guild Install／`applications.commands` 步驟安裝完成，尚未以正式真實指令驗證。
- 使用者回報正式部署網址 `diary-production.oscar940327.workers.dev` 與版本前綴 `5021c2d7`；完整版本 ID 尚待補齊。Agent 對正式入口發送無簽章 JSON `{"type":1}`，實際 HTTP 401、本文 `Invalid request signature`，符合預期；同時對測試入口重做相同檢查，也回 401。這項結果只證明測試入口仍可連線並拒絕無簽章請求，不代替測試 `/ping` 仍可用的人工確認。
- 使用者依正式註冊命令及正式入口設定步驟回覆成功，正式 guild `/ping` 註冊與 Discord 入口儲存驗證已完成；此項為使用者人工操作回報，Agent 沒有代為操作。
- 使用者回報正式手機／電腦、兩個頻道、3 秒私人回覆、無公開回覆與無私訊指令等驗收皆正確，並確認測試 `/ping` 仍正常，6.4 通過。沒有第二帳號，正式私人拒絕人工未測，引用同份程式的既有自動測試。
- Agent 沒有代為安裝、註冊或部署；6.5 核對結果如下，所有 tasks 已完成，進度 21/21。

### 6.5 完整版本、回復方式與限制

兩組完整版本從本機 Wrangler 部署日誌的 `Current Version ID` 核對，同一份日誌各自包含對應 Worker 網址；部署日期均為 2026-11-04。

| 環境 | 完整部署版本 | 日誌證據 |
| --- | --- | --- |
| test | `157df2c9-d4b4-4af6-bea3-5c4b2beeae32` | `wrangler-2026-11-04_06-17-47_003.log` |
| production | `5021c2d7-255f-4aed-86d7-4410e533bf8a` | `wrangler-2026-11-04_09-57-50_407.log` |

上方過程中「完整 ID 待補」的狀態已由本表補齊。已對照 design 的 Migration Plan 及操作文件，核對兩環境的入口、註冊、401、人工可見性、版本及未測項目；受審查的程式、工具、測試與設定相較 `acfefce` 沒有改動，沿用 Stage 5 的 118 個測試與雙軸審查證據。

未來升級後，如需回復這次已驗收版本，分別使用：

```bash
npx wrangler rollback 157df2c9-d4b4-4af6-bea3-5c4b2beeae32 --config environments/test/wrangler.jsonc
npx wrangler rollback 5021c2d7-255f-4aed-86d7-4410e533bf8a --config environments/production/wrangler.jsonc
```

若首次部署沒有先前可用版本，清除故障應用程式的 Interactions Endpoint URL，查詢其指定 guild 的 commands，僅刪除 `name=ping`、`type=1` 的單一 command。不要整批覆寫，另一環境保持原狀。Worker 回復不會同步回復 Discord 入口、指令或憑證設定，需分別核對；具體操作依 [操作文件](../../../docs/operations/discord-bot.md)。

本次僅核對回復步驟與版本，未對正常服務實際執行 rollback 或停用。第二帳號私人拒絕人工未測；3 秒結果為使用者實測回報，未進行效能壓測。兩組未建立 D1、付費方案、自訂網域或自動部署；本 change 僅提供 `/ping`，沒有日記保存。憑證檔均受 Git 忽略，未納入此次文件提交。

## 2026-11-05 結案紀錄（歷史保留）

以下保留當時「明細未同步」的說明與本人確認；那些明細現在已由上方補回，不再列為目前缺漏。

- 使用者確認：已在另一台電腦完成測試及正式兩個環境的部署與測試。本次未由 Agent 重做部署或測試。
- 使用者進一步明確確認「整個 Stage 6 都可以算完成」，並接受遺失的討論紀錄之後補回；本次以這項本人驗收確認作為 6.1–6.5 結案依據，tasks 更新為 21/21。
- 核對時 GitHub 與本機 change 分支均為 `a131404`，未包含原始部署驗收紀錄；使用者目前無法取得另一台電腦，直接在這台保存確認結果，不要求取回原電腦。
- 部署版本、實際部署日期、入口、指令 ID、逐次延遲及第二帳號人工檢查結果未留存於此 repo，日後再補；不把未留存的細項寫成 Agent 已逐項查證。使用者接受此紀錄限制後結案。

| task | 本次結案依據 |
| --- | --- |
| 6.1 | 使用者確認整組完成；兩個環境的實際目標及帳號方案明細日後補記，不由設定檔名稱推斷遠端實值。 |
| 6.2 | 使用者確認測試環境已部署並完成測試；本次不重做指令註冊或入口設定。 |
| 6.3 | 使用者確認測試已完成；原始逐項人工驗收紀錄未留存，不補造各裝置、頻道或延遲數字。 |
| 6.4 | 使用者確認正式環境亦已部署並完成測試；本次未重新存取或改動正式環境。 |
| 6.5 | 已核對設計與操作文件的回復安排，記錄目前結果及缺少原始紀錄的限制；使用者明確接受 Stage 6 完成。未執行回復演練，不宣稱已演練。 |

回復方式仍依 [操作文件](../../../docs/operations/discord-bot.md)：有上一個可用版本時回復指定 Worker；首次部署無可回復版本時，移除對應 Discord 入口並停用其單一 `/ping`。Worker 與 Discord 設定須分別處理。

合併前另在這台重跑 118 個測試、typecheck 與兩組打包 dry run，均通過，詳見 [複查紀錄](review.md)。這些是本機證據，與使用者已完成的雲端驗收分開記錄。

後補討論紀錄可從最新 `main` 開 `docs/restore-bootstrap-notes` 分支，補入對應月份後另發 PR；不需要保留或再次合併本 change 的原實作分支。
