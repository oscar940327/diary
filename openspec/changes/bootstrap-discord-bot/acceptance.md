# Stage 6 測試環境驗收紀錄

更新日期：2026-11-03。此紀錄只涵蓋本輪授權的 6.1–6.3；6.4–6.5 不在本輪範圍。
目前尚未部署、註冊真實指令或完成人工驗收，tasks 6.1–6.3 保持未勾選。

## 前置與目標

- Stage 5 已通過，產品實作版本為 `acfefce1430c02b44e5b095c13658c972e33f4e5`，見 [審查紀錄](review.md)。
- 使用者已授權測試環境部署與驗收，明確不部署正式環境；Cloudflare 帳號已由使用者建立，Discord 測試設定仍待準備。使用者改為親自操作外部服務，由 Agent 提供步驟，不再控制瀏覽器。
- 首次縮小 scopes 後的登入要求被自動核准審查拒絕；使用者明確同意帳號資訊讀取、Worker 程式修改與執行紀錄讀取權限後，重新登入成功，`wrangler whoami` 已確認帳號及 scopes（`account:read`、`user:read`、`workers_scripts:write`、`workers_tail:read`、`offline_access`）。未取得其他服務的寫入權限。
- 已建立空白且受 Git 忽略的 `environments/test/.dev.vars` 與 `.env.registration`（權限 600）；尚無真實設定，正式設定檔未修改。

| 項目 | 測試目標 | 正式目標 |
| --- | --- | --- |
| Cloudflare 帳號／實際方案 | 已建立並確認單一登入帳號；實際方案待使用者核對 | 本輪不操作 |
| Worker 名稱 | 設定為 `diary-test`，遠端尚未建立／核對 | 設定為 `diary-production`，本輪不部署 |
| Discord 應用程式 | 待建立及核對 | 待確認；不得與測試共用應用程式或 token |
| 擁有者／私人伺服器 | 待確認 | 本輪不操作 |
| 入口網址／部署版本／指令 ID | 尚無 | 本輪不操作 |

## 免費限制與操作邊界（6.1，部分準備）

- 2026-11-03 核對官方文件：Workers Free 每帳號每日 100,000 次請求，UTC 午夜重設；HTTP 請求 CPU 時間上限 10 ms，網路等待不算 CPU 時間。實際帳號方案與剩餘額度仍待登入後確認，不能用文件查核代替帳號查核。
- 本輪只使用免費方案與測試 Worker 的 `workers.dev` 網址，不新增 D1、付費方案、自訂網域或自動部署。
- 來源：[Workers 限制](https://developers.cloudflare.com/workers/platform/limits/)、[Workers 計價](https://developers.cloudflare.com/workers/platform/pricing/)。

## 實際結果（尚未執行）

| task | 驗收 | 狀態 |
| --- | --- | --- |
| 6.1 | 真實帳號方案、目標及兩組應用程式隔離核對 | 已登入，待方案核對與 Discord 設定 |
| 6.2 | 真實目標註冊 dry run、測試部署與單一 guild `/ping` 註冊 | 未執行 |
| 6.2 | Discord 入口驗證、無簽章 POST 回 401、正式設定未變 | 未執行 |
| 6.3 | 手機、電腦及另一文字頻道皆於 3 秒內收到私人 `Pong!` | 未執行 |
| 6.3 | 無公開回覆、無私訊指令及第二帳號拒絕檢查 | 未執行；第二帳號可用性待確認 |

## 本次停留位置與接續方式

- Cloudflare 帳號建立及 Wrangler 登入已完成；本次只記錄進度，不繼續操作外部服務。
- 已提供建立 `Diary Test` 應用程式、取得 Application ID／Public Key／Bot token，以及建立私人伺服器、複製擁有者／伺服器 ID 的操作步驟；尚未收到使用者完成確認。
- 本機核對：`environments/test/.dev.vars` 四個欄位、`.env.registration` 三個測試欄位目前皆為空白，兩個檔案均受 Git 忽略。
- 下次先由使用者完成 Discord 測試設定並填入上述檔案，同時核對 Cloudflare 免費方案與環境隔離；再核對真實目標 dry run，依序完成 6.2 測試部署／入口及 6.3 人工驗收，不進入正式部署。

操作方式見 [操作文件](../../../docs/operations/discord-bot.md)。這次可提交的是進度與驗收文件，未包含產品程式變更或雲端憑證。
