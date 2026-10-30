# Diary

Diary 是私人生活紀錄與記憶系統。新版先以 Discord 指令操作，
支援手機與電腦記錄、閱讀與查詢，保留未來 Agent、提醒和網頁入口的擴充方向。

## 目前狀態

`main` 已開始 v2 重建的規劃，技術選擇為 **TypeScript + Hono +
Cloudflare Workers + D1**；第一版不做獨立網頁，以免費方案額度為限制。

目前仍是規劃階段。既有 `src/diary_api/`、`tests/`、`supabase/`、
Python 設定與 CI 屬於 v1，暫留作參考；它們不是已完成的 TypeScript Bot。
新版安裝、測試及部署指令會隨各張實作 Ticket 加入，請勿把舊版測試通過
當成新版已完成。

## 從哪裡開始

- [目前方向與未決問題](DISCUSSION.md)
- [歷史討論索引](docs/discussions/README.md)
- [領域用語](CONTEXT.md)
- [新版架構決策 ADR 0018](docs/adr/0018-rebuild-as-a-discord-command-bot-on-workers.md)
- [新版規格草稿](.scratch/diary-v2/spec.md)
- [開發流程](docs/agents/development-workflow.md)

## 舊版保存

本機 `v1` 分支的 `899f5d4` 保存舊程式、文件與重建前的討論。
原 `origin/ticket-09-trash-management` 另外保留，沒有合併。

舊版採 FastAPI、Supabase 與個人網站介面；需要操作時，先切換到完整的
`v1` 版本，再閱讀 [v1 操作說明](docs/archive/v1/README.md)。
[舊版完整背景](docs/archive/v1/CONTEXT.md)、
`.scratch/diary/` 和 ADRs 0001-0017 都是歷史參考，不是新版待辦清單。

本次重建尚未部署雲端資源，也沒有搬移或刪除正式私人紀錄。
