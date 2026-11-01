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
- 每個 change 先從 `main` 建立專用分支，再實作、commit 並透過 PR 審查，不直接在 `main` 提交實作。
- 希望用多個小型 OpenSpec change 逐步開發，先看拆分與順序，不把整個專案放在同一個 change。
- 前三個近期 change 確定是 Bot 與部署、日記記錄、日期查閱；後續 change 希望先保存大綱，不先寫 tasks。
- 已同意在 PR #2 一起刪除歷史 ADR，不另切回 main 或拆分清理；需要舊內容時查閱 `v1`。

## 分支與實作現況

- `v1` 保存清理前的完整版本，最新保存點是 `a47b662`。
- 目前位於 `change/bootstrap-discord-bot`；本機及遠端 `main` 仍在實作前的 `116c9d8`，實作保存在 change 分支。
- Ticket 09 的遠端分支與本機遠端追蹤參照已依使用者要求刪除，沒有合併；最後版本為 `aca739e`，舊 PR #1 已關閉。
- 舊版 Python 後端、測試、Supabase、CI 與套件設定已從 `main` 移除。
- OpenSpec 已初始化；`bootstrap-discord-bot` 已補齊 proposal、specs、design 與 tasks，其他七個 change 維持 metadata 與 proposal 大綱。
- `bootstrap-discord-bot` Stage 1–2 已完成，進度 4/21 tasks；44 個本機 Workers 測試、typecheck 與本機打包 dry run 通過。
- 現行規劃與進度在 `openspec/changes/`；早期 `.scratch/diary-v2/` 草稿與舊 `.scratch/diary/` 留作歷史參考，ADR 由 `v1` 保存，均不作新版工作佇列。
- 尚未建立正式 Workers／D1 資源，尚未部署新版；Stage 1–2 實作與後續文件提交已在 change 分支，檢查時本機 HEAD 與遠端追蹤分支一致。
- 2026-11-01 已查核 GitHub：`v1` 在遠端，版本是 `a47b662`；遠端 `main` 是 `116c9d8`，先前的實作 commit 尚未推到 main。

## 尚待決定

- 第一版必備指令，以及修改、版本歷史、刪除／還原、匯出與備份的範圍。
- 補寫日期、時區、長文與大量查詢結果的操作方式。
- Agent 是否隨首版上線；免費模型的額度、品質與私人資料處理條件。
- 是否已有私人紀錄需要遷移，以及遷移與還原的驗收方式。
- `.scratch` 與其他舊文件是否另行清理，尚未決定；歷史 ADR 已同意在 PR #2 移除。
- `bootstrap-discord-bot` 的實際環境 ID、Worker 名稱與憑證，待未來設定；不影響目前規劃。

## 下一步

[Draft PR #2](https://github.com/oscar940327/diary/pull/2) 已做 Stage 1–2 的雙軸獨立審查，比較起點為 `116c9d8ebfb22829fe7b96891b244dc5d763d71d`，HEAD 為 `cddebaebe6cba36fdc384045b0567138b7377056`。

- Stage 1–2 功能未發現缺陷；本輪重新驗證 44 個測試、typecheck、OpenSpec 嚴格驗證及 Wrangler 本機打包 dry run 均通過。
- Standards 與 Spec 原先都指出同一項 P2：歷史 ADR 刪除不在原審查範圍，文件也稱未納入。使用者已明確接受刪除留在 PR #2，此範圍 finding 已解除；本機文件已同步，GitHub PR 說明仍待改成包含 ADR 刪除。
- Stage 1–2 的提前審查在新確認範圍下通過，沒有其他已知 blocking finding。下一步可由使用者指定 apply Stage 3，無須為這次文件調整重跑整套程式審查。
- 審查結果、範圍調整與驗證限制見 [本月紀錄](docs/discussions/2026-11.md)。目前待提交的是文件變更，尚未 commit 或 push。

這次是 Stage 1–2 的提前審查，不代表 Stage 5 完成；Stage 3–6 與其他七個 change 保持原進度，尚未部署或合併 PR。

## 討論文件如何維持精簡

- 本文件維持約 80 行以內，只更新目前決定、未決問題與下一步。
- 每次討論摘要寫入 `docs/discussions/YYYY-MM.md`，歷史較長時再分冊。
- 技術選擇集中寫在白話的 `docs/tech-stack.md`；功能細節與工作放 OpenSpec 的 specs、design 與 tasks。
