# Diary 目前方向

更新日期：2026-11-26。這份文件只放現況，不累積完整對話。
[技術選擇](docs/tech-stack.md)｜[討論索引](docs/discussions/README.md)｜[第一個 change](openspec/changes/archive/2026-11-18-bootstrap-discord-bot/proposal.md)

## 已確認

- 在 `main` 重建 Diary，採用 TypeScript、Hono、Cloudflare Workers 與 D1。
- 第一版是 Discord 指令式 Bot，現階段不製作獨立網頁。
- `bootstrap-discord-bot` 第一版只在自己的私人 Discord 伺服器使用，不支援 Bot 私訊。
- 指令由後端核對擁有者帳號 ID 與指定伺服器 ID；`/ping` 不限定單一文字頻道。
- 本次 `/ping` 成功回覆與無權使用提示，都只讓操作者本人看見；日記頻道訊息另行規劃。
- 手機與電腦都能記錄生活瑣事、滑動閱讀過往內容，也能按日期查閱。
- 希望零付費運作，不使用 Supabase，不自動改用付費方案。
- 保留測試與正式兩組環境，銜接未來真實日記的保存；用途與原因見 [技術選擇](docs/tech-stack.md)。
- Diary 保存私人紀錄；note-garden 展示可公開的筆記與知識。
- 考慮未來 Agent、提醒與網頁入口的擴充性，核心日記邏輯不綁定 Discord。
- 採 OpenSpec 規格驅動開發，直接以 tasks 的編號分組控制範圍；每次 apply 由使用者指定 stage，不額外建立 tickets 或 ADR，保留 TDD 與新 session 獨立審查。
- 每個 change 先從 `main` 建立專用分支，再實作、commit 並透過 PR 審查，不直接在 `main` 提交實作。
- 希望用多個小型 OpenSpec change 逐步開發，先看拆分與順序，不把整個專案放在同一個 change。
- 前三個近期 change 確定是 Bot 與部署、日記記錄、日期查閱；後續 change 希望先保存大綱，不先寫 tasks。
- 日記使用 `/record` 開多行表單，內容必填、日期選填；採台北日期，允許補寫但不接受未來，實際建立時間另存。
- 每筆最多 4,000 字元，原文保存 D1、長文分段顯示；失敗私下盡量一句說明保存狀態、原因與解法，提供「重試顯示」按鈕。
- 已同意在 PR #2 一起刪除歷史 ADR，不另切回 main 或拆分清理；需要舊內容時查閱 `v1`。


## 分支與實作現況

- `main` 為 Diary v2，舊版保存在 `v1` 的 `a47b662`；歷史 Ticket 09、`.scratch/` 與 ADR 不作新版工作佇列。
- [PR #2](https://github.com/oscar940327/diary/pull/2) 已於台灣時間 2026-11-06 合併，merge commit 為 `99018c2`。本次文件補記從更新後的 `main` 建立 `docs/restore-bootstrap-notes`，透過獨立文件 PR 交付。
- `bootstrap-discord-bot` Stage 1–6 已完成，21/21。新 session Stage 5 審查與 11 月 5 日合併前雙軸複查均為 0 findings；產品程式相較 `acfefce` 沒有變動。
- 測試及正式 Worker 已部署、驗收。兩組完整版本、入口、無簽章 401 與手機／電腦私人回覆證據已於 11 月 9 日補回 [驗收紀錄](openspec/changes/archive/2026-11-18-bootstrap-discord-bot/acceptance.md)。這是恢復既有紀錄，本次未重新操作雲端。
- 沒有第二帳號，人工拒絕檢查未執行，已有後端自動測試證據；未實際演練 rollback，回復步驟與版本已核對。
- 11 月 5 日「明細未同步」的本人確認與結案紀錄保留為歷史，不再作為目前缺漏；新增的合併前複查見 [review.md](openspec/changes/archive/2026-11-18-bootstrap-discord-bot/review.md)。
- `bootstrap-discord-bot` 已於 2026-11-18 歸檔至 `openspec/changes/archive/2026-11-18-bootstrap-discord-bot/`，能力規格同步至 `openspec/specs/discord-command-access/spec.md`；歸檔 PR #4 已合併，本機 main 已同步。
- `capture-diary-entry` 已完成 Stage 1–2，進度 9/26。本機 Workers 已驗證 `/record` 表單、內容與日期檢查、私人保存結果和 D1 寫入。其餘六個 change 維持提案大綱，雲端 D1 留待部署驗收。

## 尚待決定

- 日記兩組真實 D1／頻道目標及雲端驗收時間，留到部署驗收時核對；不影響目前規劃。
- 修改、版本歷史、刪除／還原、匯出與備份的範圍，以及是否需遷移私人紀錄。
- Agent、提醒及網頁的開始時機，免費模型的品質與額度。
- `.scratch` 與其他舊文件是否另行清理。

## 下一步

- `capture-diary-entry` 接下來是 Stage 3 的私人頻道顯示與手動重試。由使用者指定下一輪實作範圍，詳見 [tasks](openspec/changes/capture-diary-entry/tasks.md)。
- 操作見 [Discord Bot 文件](docs/operations/discord-bot.md)，歷史與最新補記見 [討論索引](docs/discussions/README.md)。

## 討論文件維護

本文件保持約 80 行以內；每次討論摘要存入當月分冊。技術選擇集中在白話技術文件，詳細行為與工作留在 OpenSpec。
