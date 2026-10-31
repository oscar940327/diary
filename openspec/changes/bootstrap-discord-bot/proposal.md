# Proposal

近期優先；本次補齊規劃文件，尚未實作。

## Why

先確認 Discord 指令能抵達後端並得到回覆，讓後續日記功能有可用的入口。
同時把請求驗證與擁有者限制納入起點，避免私人功能上線後才補權限。

## What Changes

- 以既定的 TypeScript／Hono／Cloudflare Workers 建立指令入口。
- 驗證每次請求的 Discord 簽章，支援 Discord 設定入口時的協定 `PING`／`PONG`。
- 指令只在自己的私人伺服器使用；後端同時核對擁有者帳號 ID 與指定伺服器 ID，不支援私訊。
- 提供 `/ping` 確認連通，不綁定單一文字頻道；成功與無權使用提示都只讓操作者本人看見。
- 分開本機測試、測試 Bot／Workers 與正式 Bot／Workers 的設定；憑證不進版本控制。
- 規劃本機自動測試及未來真實連線驗收；本次不建立資源或部署。

## Capabilities

### New Capabilities

- `discord-command-access`：接收 Discord 指令、驗證請求與擁有者，並回覆連通檢查。

### Modified Capabilities

目前沒有既有能力規格需要修改。

## Impact

後續會涉及 Bot 後端、兩組 Discord 應用程式、Workers 設定、指令註冊工具與操作文件。
只建立共用指令入口，不在這個 change 決定日記資料表。
技術選擇與原因以 [技術文件](../../../docs/tech-stack.md) 為準；本 change 不重新選框架。

## Non-goals

- 不保存或查詢日記，不加入 Agent、提醒或獨立網頁。
- 不啟動需要持續連線的 discord.js Client。
- 不處理舊版資料遷移，也不建立付費服務。
- 不建立 D1 資料表，不要求自訂網域、本機公開通道或自動部署流程。

## Dependencies

- **必要前置**：沒有其他功能 change；本機自動測試使用測試用金鑰，不依賴真實帳號憑證。未來雲端驗收另需兩組可設定的 Discord 應用程式、Workers 環境與擁有者／伺服器 ID。
- **建議順序**：第 1 個，先確認真實指令與部署方式能運作，再加入日記功能。

## Open Questions

影響本 change 行為與驗收的問題已釐清：私人伺服器、擁有者與伺服器雙重限制、
不限制單一文字頻道、指令回覆僅本人可見，以及測試／正式環境分離。

實際應用程式 ID、擁有者 ID、伺服器 ID、Worker 名稱與憑證值，留到未來設定環境時填入；
這些值不影響目前規格與任務拆分，不在文件中放入真實憑證。
