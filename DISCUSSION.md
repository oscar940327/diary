# Diary 目前方向

更新日期：2026-10-30。這份文件只放現況，不累積完整對話。
[歷史討論與記錄方式](docs/discussions/README.md)｜[新版架構決策](docs/adr/0018-rebuild-as-a-discord-command-bot-on-workers.md)｜[新版規格草稿](.scratch/diary-v2/spec.md)

## 已確認

- 在 `main` 重建 Diary，採用 TypeScript、Hono、Cloudflare Workers 與 D1。
- 第一版是 Discord 指令式 Bot，現階段不製作獨立網頁。
- 手機與電腦都能記錄生活瑣事、滑動閱讀過往內容，也能按日期查閱。
- 希望零付費運作，不使用 Supabase，不自動改用付費方案。
- Diary 保存私人紀錄；note-garden 展示可公開的筆記與知識。
- 考慮未來 Agent、提醒與網頁入口的擴充性，核心日記邏輯不綁定 Discord。
- 採規格驅動開發：釐清範圍、寫規格、拆票、逐票 TDD 與獨立審查。

## 分支與實作現況

- `v1` 已提交保存重建前的程式、文件與討論，保存點是 `899f5d4`。
- 目前位於 `main`，從 v1 保存點開始整理新版文件。
- 原 `origin/ticket-09-trash-management` 另留，沒有合併。
- 既有 Python、Supabase 程式與 CI 暫留作參考，尚未替換成新版 Bot。
- 新版規劃在 `.scratch/diary-v2/`；舊 `.scratch/diary/` 是 v1 紀錄。
- 尚未建立正式 Workers／D1 資源，尚未部署新版。這次提交先保存於本機。

## 尚待決定

- 第一版必備指令，以及修改、版本歷史、刪除／還原、匯出與備份的範圍。
- 補寫日期、時區、長文與大量查詢結果的操作方式。
- Agent 是否隨首版上線；免費模型的額度、品質與私人資料處理條件。
- 是否已有私人紀錄需要遷移，以及遷移與還原的驗收方式。

## 下一步

以 Discord 記錄、私人頻道閱讀和 `/day` 查詢為第一條候選流程，
完成新版規格，再拆成可獨立驗收的 Tickets。詳細行為尚未確認，
不能直接沿用 v1 的整份 MVP 或接著實作舊 Ticket 09。

## 討論文件如何維持精簡

- 本文件維持約 80 行以內，只更新目前決定、未決問題與下一步。
- 每次討論摘要寫入 `docs/discussions/YYYY-MM.md`，歷史較長時再分冊。
- 正式架構放 ADR；功能細節放規格與 Tickets，討論紀錄保留結論和連結。
