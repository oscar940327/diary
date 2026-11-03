# Diary 目前方向

更新日期：2026-11-03。這份文件只放現況，不累積完整對話。
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
- `bootstrap-discord-bot` Stage 1–5 已完成，進度 16/21 tasks；Stage 5 雙軸獨立審查各 0 項 findings，Node.js 24 下 118 個測試、typecheck、兩組打包 dry run 與 OpenSpec 嚴格驗證通過。
- 現行規劃與進度在 `openspec/changes/`；早期 `.scratch/diary-v2/` 草稿與舊 `.scratch/diary/` 留作歷史參考，ADR 由 `v1` 保存，均不作新版工作佇列。
- 尚未建立正式 Workers／D1 資源，尚未部署新版；Stage 4 實作提交為 `acfefce`，Stage 5 審查文件已提交為 `0f76274`，本機較遠端追蹤分支多 2 個 commit；討論文件原有未提交更新已保留。
- 2026-11-01 已查核 GitHub：`v1` 在遠端，版本是 `a47b662`；遠端 `main` 是 `116c9d8`，先前的實作 commit 尚未推到 main。

## 尚待決定

- 第一版必備指令，以及修改、版本歷史、刪除／還原、匯出與備份的範圍。
- 補寫日期、時區、長文與大量查詢結果的操作方式。
- Agent 是否隨首版上線；免費模型的額度、品質與私人資料處理條件。
- 是否已有私人紀錄需要遷移，以及遷移與還原的驗收方式。
- `.scratch` 與其他舊文件是否另行清理，尚未決定；歷史 ADR 已同意在 PR #2 移除。
- `bootstrap-discord-bot` 的實際環境 ID 與憑證待設定；測試 Worker 暫定沿用設定中的 `diary-test`，遠端仍待核對。

## 下一步

[Draft PR #2](https://github.com/oscar940327/diary/pull/2) 尚未合併。本次在新 session 完成完整 Stage 1–4 的雙軸獨立審查，比較 `116c9d8ebfb22829fe7b96891b244dc5d763d71d...acfefce1430c02b44e5b095c13658c972e33f4e5`，涵蓋 48 個檔案。

- Stage 5 的 Standards 與 Spec 由兩個獨立代理平行審查，各 0 項 findings，沒有阻擋問題；完整結果與規格情境對照見 [審查紀錄](openspec/changes/bootstrap-discord-bot/review.md)。
- Stage 5 的 5.1–5.3 已完成，既有 118 個回歸測試及本機檢查通過。
- 本輪已指定並授權 Stage 6 的 6.1–6.3，只建立及驗收測試環境，不部署正式環境。Cloudflare 帳號已建立，使用者同意登入權限後 Wrangler 已登入；方案與 Discord 設定待核對。後續由使用者親自操作外部服務，Agent 提供步驟。
- 已備妥受 Git 忽略的空白測試設定檔，目前停在使用者建立 `Diary Test`／私人伺服器及填入 ID、Public Key 與 token；尚未部署或真實註冊，6.1–6.3 均未勾選。下次從此處接續，詳見 [測試環境驗收紀錄](openspec/changes/bootstrap-discord-bot/acceptance.md)。
- 操作說明見 [操作文件](docs/operations/discord-bot.md)，歷史 TDD、乾淨環境驗收及本輪摘要見 [本月第 2 冊](docs/discussions/2026-11-part-02.md)。

Stage 5 已完成；Stage 6 正在準備測試環境，進度仍為 16/21，尚未部署或合併 PR。

## 討論文件如何維持精簡

- 本文件維持約 80 行以內，只更新目前決定、未決問題與下一步。
- 每次討論摘要寫入 `docs/discussions/YYYY-MM.md`，歷史較長時再分冊。
- 技術選擇集中寫在白話的 `docs/tech-stack.md`；功能細節與工作放 OpenSpec 的 specs、design 與 tasks。
