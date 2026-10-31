# Diary 目前方向

更新日期：2026-10-31。這份文件只放現況，不累積完整對話。
[這次的技術選擇](docs/tech-stack.md)｜[歷史討論與記錄方式](docs/discussions/README.md)｜[第一個 change 大綱](openspec/changes/bootstrap-discord-bot/proposal.md)

## 已確認

- 在 `main` 重建 Diary，採用 TypeScript、Hono、Cloudflare Workers 與 D1。
- 第一版是 Discord 指令式 Bot，現階段不製作獨立網頁。
- 手機與電腦都能記錄生活瑣事、滑動閱讀過往內容，也能按日期查閱。
- 希望零付費運作，不使用 Supabase，不自動改用付費方案。
- Diary 保存私人紀錄；note-garden 展示可公開的筆記與知識。
- 考慮未來 Agent、提醒與網頁入口的擴充性，核心日記邏輯不綁定 Discord。
- 採規格驅動開發：釐清範圍、寫規格、拆票、逐票 TDD 與獨立審查。
- 希望用多個小型 OpenSpec change 逐步開發，先看拆分與順序，不把整個專案放在同一個 change。
- 前三個近期 change 確定是 Bot 與部署、日記記錄、日期查閱；後續 change 希望先保存大綱，不先寫 tasks。

## 分支與實作現況

- `v1` 保存清理前的完整版本，最新保存點是 `a47b662`。
- 目前位於 `main`，從乾淨的程式環境重新開始。
- 原 `origin/ticket-09-trash-management` 另留，沒有合併。
- 舊版 Python 後端、測試、Supabase、CI 與套件設定已從 `main` 移除。
- OpenSpec 已初始化，八個 change 都有 metadata 與 `proposal.md`，尚未建立 specs、design 或 tasks。
- change 大綱在 `openspec/changes/`；先前 `.scratch/diary-v2/` 草稿尚未整併，舊 `.scratch/diary/` 是 v1 紀錄。
- 尚未建立正式 Workers／D1 資源，尚未部署新版。這次提交先保存於本機。
- 2026-10-31 最新查詢 GitHub：`v1` 已在遠端，版本是 `a47b662`；遠端 `main` 仍在 `36c62ae`。

## 尚待決定

- 第一版必備指令，以及修改、版本歷史、刪除／還原、匯出與備份的範圍。
- 補寫日期、時區、長文與大量查詢結果的操作方式。
- Agent 是否隨首版上線；免費模型的額度、品質與私人資料處理條件。
- 是否已有私人紀錄需要遷移，以及遷移與還原的驗收方式。
- 文件是否再簡化：移除舊 ADR，並把 `docs/agents/` 的必要規則合進 `AGENTS.md`，尚未決定。
- OpenSpec change 與原 `.scratch/diary-v2/` 草稿、工作流程如何整合。

## 下一步

目前八份大綱與 OpenSpec 初始化檔案尚未提交，建議先保存這個規劃起點。
接著由使用者執行 prompt，只細化 `bootstrap-discord-bot`，釐清入口、擁有者限制與驗收方式，
再補齊該 change 的規格、設計與 tasks。其他七個先保留大綱，目前未開始實作。

## 討論文件如何維持精簡

- 本文件維持約 80 行以內，只更新目前決定、未決問題與下一步。
- 每次討論摘要寫入 `docs/discussions/YYYY-MM.md`，歷史較長時再分冊。
- 技術選擇集中寫在白話的 `docs/tech-stack.md`；功能細節放規格與 Tickets。
