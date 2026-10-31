# Diary 目前方向

更新日期：2026-11-01。這份文件只放現況，不累積完整對話。
[這次的技術選擇](docs/tech-stack.md)｜[歷史討論與記錄方式](docs/discussions/README.md)｜[第一個 change 大綱](openspec/changes/bootstrap-discord-bot/proposal.md)

## 已確認

- 在 `main` 重建 Diary，採用 TypeScript、Hono、Cloudflare Workers 與 D1。
- 第一版是 Discord 指令式 Bot，現階段不製作獨立網頁。
- `bootstrap-discord-bot` 第一版只在自己的私人 Discord 伺服器使用，不支援 Bot 私訊。
- 指令由後端核對擁有者帳號 ID 與指定伺服器 ID；`/ping` 不限定單一文字頻道。
- 本次 `/ping` 成功回覆與無權使用提示，都只讓操作者本人看見；日記頻道訊息另行規劃。
- 手機與電腦都能記錄生活瑣事、滑動閱讀過往內容，也能按日期查閱。
- 希望零付費運作，不使用 Supabase，不自動改用付費方案。
- Diary 保存私人紀錄；note-garden 展示可公開的筆記與知識。
- 考慮未來 Agent、提醒與網頁入口的擴充性，核心日記邏輯不綁定 Discord。
- 採 OpenSpec 規格驅動開發，直接以 tasks 的編號分組控制範圍；每次 apply 由使用者指定 stage，不額外建立 tickets 或 ADR，保留 TDD 與新 session 獨立審查。
- 希望用多個小型 OpenSpec change 逐步開發，先看拆分與順序，不把整個專案放在同一個 change。
- 前三個近期 change 確定是 Bot 與部署、日記記錄、日期查閱；後續 change 希望先保存大綱，不先寫 tasks。

## 分支與實作現況

- `v1` 保存清理前的完整版本，最新保存點是 `a47b662`。
- 目前位於 `main`，從乾淨的程式環境重新開始。
- 原 `origin/ticket-09-trash-management` 另留，沒有合併。
- 舊版 Python 後端、測試、Supabase、CI 與套件設定已從 `main` 移除。
- OpenSpec 已初始化；`bootstrap-discord-bot` 已補齊 proposal、specs、design 與 tasks，其他七個 change 維持 metadata 與 proposal 大綱。
- 現行規劃與進度在 `openspec/changes/`；早期 `.scratch/diary-v2/` 草稿、舊 `.scratch/diary/` 與 ADR 留作歷史參考，不作新版工作佇列。
- 尚未建立正式 Workers／D1 資源，尚未部署新版。這次提交先保存於本機。
- 2026-10-31 最新查詢 GitHub：`v1` 已在遠端，版本是 `a47b662`；遠端 `main` 仍在 `36c62ae`。

## 尚待決定

- 第一版必備指令，以及修改、版本歷史、刪除／還原、匯出與備份的範圍。
- 補寫日期、時區、長文與大量查詢結果的操作方式。
- Agent 是否隨首版上線；免費模型的額度、品質與私人資料處理條件。
- 是否已有私人紀錄需要遷移，以及遷移與還原的驗收方式。
- 歷史 ADR、`.scratch` 與其他舊文件是否另行清理，尚未決定；本次只修正新版流程與文件指引。
- `bootstrap-discord-bot` 的實際環境 ID、Worker 名稱與憑證，待未來設定；不影響目前規劃。

## 下一步

`bootstrap-discord-bot` 已改為六個 stage：工具設定、入口驗證、權限回覆、環境工具、獨立審查、部署驗收。
建議先查看新版 tasks，再於新 session 指定只 apply Stage 1–2；完成驗證入口即停止，使用者 `/ping` 留到 Stage 3。
所有 tasks 尚未執行；Stage 5 另開 session 審查，通過後才進 Stage 6。其他七個 change 維持大綱，本次未實作、部署、commit 或 push。

## 討論文件如何維持精簡

- 本文件維持約 80 行以內，只更新目前決定、未決問題與下一步。
- 每次討論摘要寫入 `docs/discussions/YYYY-MM.md`，歷史較長時再分冊。
- 技術選擇集中寫在白話的 `docs/tech-stack.md`；功能細節與工作放 OpenSpec 的 specs、design 與 tasks。
