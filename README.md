# Diary

Diary 是私人生活紀錄與記憶系統，先透過 Discord 指令使用。
手機和電腦都能記錄與閱讀，未來再加入 Agent、提醒或網頁入口。

## 這次怎麼做

前端、後端、部署和資料庫的選擇，集中記在
[白話技術文件](docs/tech-stack.md)。

`main` 已移除舊版程式、測試、套件與 CI，從乾淨的程式環境開始。
目前已完成第一個 change 的 Stage 1–5：驗證入口、擁有者的私人 `/ping`、指令註冊工具、獨立環境設定、操作文件與雙軸獨立審查，進度為 16/21 tasks。
審查結果見 [Stage 5 紀錄](openspec/changes/bootstrap-discord-bot/review.md)；尚未部署或在真實 Discord 驗收，Stage 6 保持待辦。
依 OpenSpec 的規格與 tasks 分階段實作，每次自行指定要做哪些 stage。

## 本機檢查

使用 Node.js 24，安裝鎖定的依賴後執行：

```bash
npm ci
npm run typecheck
npm test
```

測試分為本機 Workers 行為與 Node.js 操作工具，使用測試用簽署金鑰並攔截對外請求，不需要真實 Discord 或 Cloudflare 憑證。

兩組環境都可只在本機打包：

```bash
npm run build:test
npm run build:production
```

本機啟動、註冊 dry run、設定用途、未來部署與回復步驟，見 [Discord Bot 操作說明](docs/operations/discord-bot.md)。

## 從哪裡開始

- [這次的技術選擇](docs/tech-stack.md)
- [目前方向與未決問題](DISCUSSION.md)
- [OpenSpec changes](openspec/changes/)：各次變更的規劃與工作清單。
- [第一個 change 的 tasks](openspec/changes/bootstrap-discord-bot/tasks.md)
- [領域用語](CONTEXT.md)
- [歷史討論](docs/discussions/README.md)
- [開發流程](docs/agents/development-workflow.md)

## 舊版保存

`v1` 分支的 `a47b662` 保存清理前的完整版本。
舊程式、測試、套件與部署設定需要查看時，切換到 `v1` 即可。
原 Ticket 09 分支已停用並刪除，沒有合併；最後版本與處理紀錄見 [歷史討論](docs/discussions/2026-11.md)。
歷史 ADR 已從新版分支移除，原始內容仍可在 `v1` 分支查看；`.scratch/` 仍留作歷史參考。新版不必另外建立 ADR 或 tickets。
