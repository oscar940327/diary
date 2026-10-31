# Proposal

後續候選；先保留方向，尚未決定開始時間或實作細節。

## Why

生活紀錄可能需要補充或更正，但直接覆蓋原文會失去以前寫過的內容。
修改與保留版本一起規劃，讓同一筆日記的變化仍可追溯。

## What Changes

- 讓擁有者選擇既有 Entry 並修改 Original Content。
- 保持 Entry 身分不變，透過 Entry Revision 保留修改前後的原文。
- 讓擁有者能分辨目前內容與先前版本。
- 一起規劃頻道顯示與日期查閱如何反映修改，避免資料庫與畫面各說各話。

## Capabilities

### New Capabilities

- `diary-entry-revisions`：修改同一筆日記並保存、查閱原文版本。

### Modified Capabilities

目前沒有既有能力規格需要修改；細化時需核對記錄與日期查閱的既有規格，補列真正受影響的能力。

## Impact

後續會涉及 D1 版本資料、既有日記轉換與 Discord 修改、查閱入口。
若匯出、搜尋或 Agent 已存在，也要檢查它們如何辨識目前內容與來源版本。

## Non-goals

- 不同時實作垃圾桶、永久刪除或多人協作。
- 不自動用 AI 改寫原文。
- 日期調整與歷史版本還原是否加入，保留另行討論。

## Dependencies

- **必要前置**：`capture-diary-entry`，需要已有穩定的 Entry 與原文。
- **建議順序**：第 5 個；先完成 `browse-diary-by-date`，較容易選取與檢查修改的紀錄。
- **建議順序**：若匯出先完成，本 change 需確認新增版本後的相容方式；不要求先有 Agent。

## Open Questions

- 在 Discord 如何選擇日記、開啟修改與查看舊版本？
- 已存在的日記如何納入版本紀錄？
- 重複送出或兩次修改互相重疊時，如何避免覆蓋較新的內容？
- 是否把修改 Entry Time 或還原舊版本納入這個 change？
