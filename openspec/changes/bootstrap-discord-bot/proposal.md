# Proposal

近期優先；本次只保存大綱，尚未實作。

## Why

先確認 Discord 指令能抵達後端並得到回覆，讓後續日記功能有可用的入口。
同時把請求驗證與擁有者限制納入起點，避免私人功能上線後才補權限。

## What Changes

- 以既定的 TypeScript／Hono／Cloudflare Workers 建立指令入口。
- 驗證請求是否來自 Discord，並限制只有擁有者能使用受保護指令。
- 提供 `/ping`，讓擁有者確認 Bot 與後端連通。
- 規劃本機檢查及 Workers 上的連通驗收；這份提案本身不部署。

## Capabilities

### New Capabilities

- `discord-command-access`：接收 Discord 指令、驗證請求與擁有者，並回覆連通檢查。

### Modified Capabilities

目前沒有既有能力規格需要修改。

## Impact

後續會涉及 Bot 後端、Discord 應用程式設定、Workers 設定與驗證。
只建立共用指令入口，不在這個 change 決定日記資料表。

## Non-goals

- 不保存或查詢日記，不加入 Agent、提醒或獨立網頁。
- 不啟動需要持續連線的 discord.js Client。
- 不處理舊版資料遷移，也不建立付費服務。

## Dependencies

- **必要前置**：沒有其他功能 change；開發時需要可設定的 Discord 應用程式與 Workers 環境。
- **建議順序**：第 1 個，先確認真實指令與部署方式能運作，再加入日記功能。

## Open Questions

- 第一版使用私人伺服器、Bot 私訊，或兩者都支援？
- 擁有者身分如何設定？是否另外限制伺服器與頻道？
- 本機測試、正式部署與敏感設定要如何分開？
