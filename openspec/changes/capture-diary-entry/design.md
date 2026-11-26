# Design

## Context

動機與使用者已確認的範圍見 [proposal.md](proposal.md)，外部行為以 [日記規格](specs/diary-entry-capture/spec.md) 與 [入口變更](specs/discord-command-access/spec.md) 為準；技術選擇沿用 [技術文件](../../../docs/tech-stack.md)。

現有程式只有 HTTP 入口、Discord 驗證／擁有者授權與 `/ping`；沒有 D1 或頻道發訊能力。入口目前拒絕表單及按鈕互動，回覆型別也僅有 PONG 與私人文字，因此必須擴充既有流程，不能只加一個指令分支。

## Goals / Non-Goals

**Goals:**

- 讓日記保存不依賴頻道發送成功，出錯後能用持久化進度恢復。
- 將日記內容／日期驗證、資料保存與 Discord 顯示分開，未來入口與查詢能重用保存資料。
- 在本機真實 D1 與 Workers runtime 驗證資料一致性，外部 Discord 請求才攔截。

**Non-Goals:**

- 不建立通用 repository 框架、任務平台、Queue、排程或新常駐服務。
- 不處理草稿、附件、版本編輯與日期瀏覽；本次日期欄只決定 Entry 的日歸屬，不推測當天事件的精確時間。
- 不宣稱 D1 與 Discord 能共同提交一個交易，也不承諾送達結果不明時絕對不重複。

## Decisions

### 1. 保留共同驗證，依互動分流

維持「共用設定 → 原始位元組簽章 → JSON／application ID → 互動結構 → 擁有者與 guild → 操作」順序。

- `/record`：立即回類型 9 的 modal，內容為多行文字，日期為選填單行 `YYYY-MM-DD`；採 Discord 目前建議的 Label 包 Text Input 格式。
- 表單送出：重新授權，做快速欄位驗證後回私人 deferred response；實際保存與顯示交給有限時的後續工作，完成後更新私人結果。
- 重試按鈕：重新授權並核對 Entry 歸屬，以本次互動的新 token 更新私人結果，不能一直沿用首次提交 token。
- `/ping` 仍直接回私人 Pong，不需要資料庫、日記頻道或發送 token；協定 PING 仍不要求 user／guild。

Hono 路由仍負責串接 HTTP 與執行環境，日記流程不要全部塞進路由。採少量職責明確的函式／模組；實際檔名由實作決定，不先搭依賴注入容器。

### 2. 日期與原文各自驗證

以 `Asia/Taipei` 及可控制的時鐘判斷提交日，不能使用主機預設時區或模糊的 `Date.parse()` 猜日期。日期欄去除外圍空白後驗證 `YYYY-MM-DD` 與真實曆日，再比較是否為未來；日期留空才取提交當下今天。

歸屬日期保存為日曆日期字串，實際建立時間另存 UTC。Entry Time 的日期部分由本欄位表達；沒有輸入事件時間就不虛構 00:00 為實際發生時刻。未來若加入時間欄，由對應 change 明確延伸。

原文只用去空白結果判斷是否全空白，通過後原字串完整保存。4,000 字元採 UTF-16 長度作保守計數，文件說明 emoji 可能占兩個單位；這是本專案的計數選擇，不假稱每個可見字都只占一個單位。測試需涵蓋上限及 emoji 邊界。

### 3. 用資料庫約束保證一個提交只有一筆

建議兩個小型資料表，確切 SQL 於 Stage 1 依測試落實：

| 資料 | 保存內容 | 目的 |
| --- | --- | --- |
| `entries` | Entry ID、應用程式／擁有者／guild、提交識別、完整原文、原始日期輸入、歸屬日期、UTC 建立時間、顯示狀態與短暫執行鎖 | 原文及恢復起點 |
| `entry_messages` | Entry ID、段落順序、固定的顯示文字、發送狀態、Discord channel／message ID、短原因碼與 nonce | 分段進度與日後訊息連結 |

每次開啟表單使用已驗證的 `/record` interaction ID 形成提交識別，放入不含原文的 modal custom ID；同一表單的重送沿用相同識別。建立 Entry 使用唯一約束及原子新增，不能只先 SELECT 再 INSERT；衝突後讀回既有資料並比對輸入，內容不同不覆寫。

相同內容但分別開啟兩個表單是兩次意圖，不能用原文雜湊當唯一鍵。重複的空白日期輸入沿用第一次保存的歸屬日期及建立時間，不能在跨日重播時改成新日期。

Entry 本身的 `pending` 顯示狀態與原文同次新增；即使之後產生片段失敗，仍有可恢復的 Entry。片段第一次產生時以 D1 batch 全部寫入；同一 Entry 的段落順序唯一，保存固定顯示文字，避免重試後因格式變化重切內容。使用參數化 SQL，原文不能拼入 SQL 或日誌。

### 4. 先保存，再有限時地發送

表單／按鈕在 Discord 初次回覆期限內先確認收到；保存與發送放入 `executionCtx.waitUntil()` 的單次有限工作，設定外部 HTTP 逾時，工作期限內結束並回報結果。不能回應後丟出沒有 `waitUntil` 的 Promise，也不能把背景工作啟動視為成功。

Stage 3 將確認、保存與頻道發送合計限制為 24 秒，再留最多 4 秒更新私人結果。確認最多 2 秒，保存等待最多 12 秒，每次頻道 HTTP 最多 3 秒，三者均受整體期限限制。D1 操作可能在停止等待後完成，重試仍沿用原提交識別。發送鎖保留 35 秒，跨越整次背景工作期限。

本次採持久化進度加手動重試，沒有排程消費者；`waitUntil` 不是可靠佇列，工作可能因平台終止或程序重啟而未完成。若連更新私人結果的請求也失敗，就不能保證使用者一定收到解釋；保留 D1 狀態與安全原因碼，能回覆時如實提示，不假稱通知已送達。

已確認保存後，將原文切成按順序的片段，每則保留日期及段號空間，整則 UTF-16 長度不超過 2,000；優先在換行附近分段，不能切斷 surrogate pair。固定片段可還原完整原文順序；資料庫原文保持不變。補寫日期只標示歸屬日，不插回舊頻道位置。

使用 Bot token 呼叫指定頻道的 Create Message，關閉 allowed mentions 與連結預覽，不讀取其他頻道訊息或開 Message Content intent。頻道顯示與私人操作回覆分開，不用回覆所在頻道推算日記目標。

### 5. 重試沿用同一筆，逐段記錄進度

Entry 以條件式 UPDATE 取得有期限的發送鎖，正常同時點擊只有一個工作者發送；其餘回覆正在處理。鎖包含工作識別，舊工作不能覆寫新工作的狀態；期限大於該次工作的最長存活時間，並用測試驗證逾期恢復。

片段成功取得 Discord message ID 才標示 sent；後續失敗保留已 sent 的片段。重試從 D1 載入固定片段，只處理未確認的部分，全部成功後重按直接回報完成。新的重試互動提供新的 token，不需要保存 interaction token 到資料庫。

每段使用穩定且符合 API 長度的 nonce 及 `enforce_nonce`，降低近期重送重複機率；它只有有限去重期間，不當成永久保證。若訊息已送達但回應遺失、或送達後 D1 更新失敗，保留 uncertain 狀態並提示「可能已送達」；再次重試可能出現重複訊息，但不能重建 Entry，也不能重送已確認片段。

若首次寫入結果不明，私人訊息不能說「已保存」；按鈕先以同一提交識別重新查證，找到才補顯示，找不到則說明目前未找到及重新填寫的辦法。不得把按鈕資料當原文直接新增日記。此處不承諾未保存的表單草稿能恢復。

### 6. 失敗訊息用一句白話

格式為「保存狀態＋已知原因＋下一步」；根據受控原因分類轉成訊息，不直接轉送外部 response body、SQL、token 或 stack。

| 情況 | 訊息示例 |
| --- | --- |
| 日期不合法 | 日記未保存，日期必須是今天或過去的有效日期，請修正後重新送出。 |
| 缺少發言權限 | 日記已保存，但機器人沒有頻道發言權限，請開啟權限後重試顯示。 |
| 無法存取頻道 | 日記已保存，但無法存取設定的日記頻道，請確認頻道與 Bot 權限後重試顯示。 |
| 確認為限流 | 日記已保存，但 Discord 暫時限制發送，請稍後重試顯示。 |
| 寫入明確失敗 | 日記未保存，資料庫目前無法使用，請保留原文並稍後重新提交。 |
| 寫入結果不明 | 保存結果未確認，暫時無法查證資料庫狀態，請稍後按重試顯示確認本次紀錄。 |
| 發送逾時 | 日記已保存，但部分訊息送達結果未明，請先查看日記頻道再決定是否重試。 |
| 無法確認原因 | 日記已保存，但顯示失敗且原因暫不明，請稍後重試顯示。 |

以上是文案範例，不表示已執行這些操作。句子可帶必要狀態或段號，但不要為追求一句而說錯保存結果；HTTP 協定或簽章錯誤維持通用 400／401／503，不對偽造請求執行業務流程。

### 7. 兩個環境，分開資料與發送設定

新增各環境的 `DB` binding、`DISCORD_DIARY_CHANNEL_ID` 與作為 Worker secret 的 `DISCORD_BOT_TOKEN`；Bot token 以前僅供註冊，這次因日記發訊才增加 Worker 使用。不能把真實值寫進 Wrangler 範例或程式。

測試／正式使用不同 D1 及私人日記頻道，沿用已分離的 Bot、Worker 與 token；可在同一私人 guild，只有擁有者與對應 Bot 具有所需存取。發送前核對頻道屬於指定 guild 且為支援的文字頻道；不能只相信任意填入的 channel ID，也不掃描私人歷史。

註冊工具新增明確環境的單一 `/record` 註冊與 dry run，保留 `/ping`，不整批覆寫。Bot 安裝／頻道權限增加發訊所需的 `bot` scope、View Channel 與 Send Messages，不要求管理員。必要設定缺失只讓日記操作停止，不讓 `/ping` 失效。

本機測試的 D1、假 Bot token 與攔截 HTTP 各自隔離，不能使用遠端 binding。沿用既有鎖定依賴，先以現有 Workers 測試整合接 D1；不要為本次規劃升級套件。

## Risks / Trade-offs

- D1 與 Discord 無共同交易 → 保存先行、分段持久化；結果不明時如實回報，不用刪日記補償。
- 多次點擊／程序中斷 → 唯一提交識別、段落唯一約束、有限鎖及手動恢復；測試並行與重啟情境。
- 按鈕所在的私人回覆被關閉或 Discord 故障 → 本版不保證恢復入口永久可見，原文及進度仍在 D1；後續日期查閱可另加恢復入口，不在本次新增查詢指令。
- Worker 被強制終止／私人回覆發送也失敗 → 無法保證每次中斷都送出一句解釋；測試可控制的錯誤，部署驗收另核對時限及 CPU 額度。
- 免費額度耗盡 → 短句提示、停止該操作，沿用既有資料；不自動升級付費或轉用其他服務。
- 回退程式造成資料遺失 → 首次只做新增型 migration，停用新指令或回退程式時保留 D1，不自動 DROP 或還原資料。

## Migration Plan

1. Stage 1–4 只在本機驗收 migrations、真實 D1 讀寫、簽章 HTTP 與攔截 Discord；建立實作分支後才動產品程式，沒有雲端建立或部署。
2. Stage 5 在新 session 獨立審查全部差異，修正阻擋問題並重跑相關驗證。
3. Stage 6 另有對應授權後，核對當時免費限制、測試 Bot／Worker／D1／頻道及最小權限；建立測試 D1，先列出並核對 migrations，才指定目標套用。
4. 先註冊 dry run，再部署測試環境及單一 `/record`；真實測試手機、電腦、補寫、長文、拒絕、重送、權限失敗與按鈕補送，並回歸 `/ping`。
5. 正式環境另有授權後，核對獨立目標及既有資料，先保存可用的資料還原點／匯出，再套用新增型 migration、部署及驗收；測試不能影響真實日記。
6. 記錄版本、資料庫與頻道目標、migrations、預期／實際結果、未測項目及回復方式，不記錄秘密或原文。失敗可停用 `/record` 或回退程式，但保留 D1 原文及進度；任何資料還原另外評估，不自動執行。

## Open Questions

- 真實資料庫名稱／ID、日記頻道 ID、部署憑證與驗收日期留到 Stage 6 核對，不影響目前行為或 tasks。
- 第二帳號是否可用，留待驗收時確認；沒有時記錄人工未測及對應自動授權測試，不假稱已人工通過。

## References

2026-11-18 查核官方文件；下列限制不取代 Stage 6 當時的帳號與額度核對。

- [Discord 表單元件與文字上限](https://docs.discord.com/developers/components/reference#text-input)：多行輸入與 4,000 字元上限，現在建議 Text Input 放在 Label 內。
- [Discord 回覆與互動 token](https://docs.discord.com/developers/interactions/receiving-and-responding)：3 秒初次回覆、15 分鐘 token 及 modal／deferred 回覆方式。
- [Discord 頻道訊息](https://docs.discord.com/developers/resources/message#create-message)：2,000 字元、allowed mentions 及有限期間的 nonce 去重。
- [Workers waitUntil](https://developers.cloudflare.com/workers/runtime-apis/context/#waituntil)：HTTP 回覆後最多延長 30 秒，不是可靠任務佇列。
- [D1 batch](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch)：多筆 prepared statements 可在同一交易中執行。
- [D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/) 與 [免費額度](https://developers.cloudflare.com/d1/platform/pricing/)：部署時核對目標與當時方案，不自動升級。
