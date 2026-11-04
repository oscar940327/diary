# Development workflow

Diary v2 使用 OpenSpec 管理規劃與實作進度。直接依 change 的 `tasks.md` 分組執行，不另外拆成 Markdown tickets，也不要求另寫 ADR。

## Active rebuild

先讀 [技術選擇](../tech-stack.md) 與 [目前方向](../../DISCUSSION.md)，再讀選定 change 的規劃文件。
目前待開發的 change 在 `openspec/changes/`；已歸檔能力的現行規格在 `openspec/specs/`。
change 的設計取捨放 `design.md`，工作與驗收放 `tasks.md`，避免另建重複文件。

`v1` 保存舊程式。`.scratch/diary/`、早期 `.scratch/diary-v2/` 草稿與 `docs/adr/` 是歷史參考，
不作為新版實作的前置流程；不接續舊 Ticket 09。只有追查歷史或使用者明確要求時才需要閱讀相關舊文件。

| 階段 | 怎麼做 | 完成條件 |
| --- | --- | --- |
| 釐清 | 用 `openspec-explore` 討論重要問題，一次問一個並附建議。 | 會影響本次行為與驗收的問題已確認。 |
| 規劃 | 依 CLI 指示建立 proposal、specs、適用的 design 與 tasks；修改既有規劃可用 `openspec-update-change`。 | 文件彼此一致，選定 change 通過驗證；其他候選 change 可維持大綱。 |
| 實作 | 用 `openspec-apply-change`，由使用者指定本次執行的 stage。 | 指定範圍的 tasks 完成驗收並更新勾選，停在指定邊界。 |
| 獨立審查 | 到 review stage 時，另開新 session 使用 `code-review`。 | 阻擋問題修正、相關檢查通過，留下複查紀錄。 |
| 真實環境驗收 | 依 tasks 的部署驗收 stage 與對應授權操作指定環境。 | 真實連線與必要人工情境有結果，未驗證項目明確保留。 |
| 歸檔 | 實作、審查與必要驗收全數完成後，使用 `openspec-archive-change`。 | change 歸檔，能力規格同步到 `openspec/specs/`。 |

## Branch workflow

開始實作 change 前，先建立或切換到從 `main` 分出的專用分支，例如 `change/bootstrap-discord-bot`。
實作 commit 放在該分支，透過 PR 提議合併到 `main`；不要直接在 `main` 提交實作。
分支操作保留工作區既有變更，無關修改另行處理，不混入這個 PR。

change 合併後才補回的討論或驗收紀錄，從最新 `main` 另開文件分支，例如 `docs/restore-bootstrap-notes`，
補進對應月份的討論檔並另發 PR。若 change 已歸檔，詳細驗收紀錄更新其歸檔路徑；
不用重開舊實作分支，也不重新合併已進入 `main` 的程式。歷史紀錄保留原討論日期，另註補記日期。

## Stage scope

`tasks.md` 的 `## 1. ...`、`## 2. ...` 等編號分組，稱為 stage；`1.1`、`1.2` 是其中的 task。
這是本專案的範圍約定，不是 OpenSpec CLI 的 stage 參數。CLI 以 task 勾選追蹤進度。
每個 change 可有不同數量的 stage，不要求全部 change 都採六組。

例如使用者可以指定「本次只做 Stage 1–2」。Agent 依該範圍執行，完成後停止；
後續再由使用者指定下一批 stage。先前已完成的前置工作不必重做。
如果沒有指定範圍，先確認要做哪些 stage，不預設執行整個 change。

## Operating rules

- 只做使用者選定的 stage；前置未完成先回報，不自行擴大到未指定的 stage。
- 有行為變更的 task 使用 TDD：確認測試因預期原因失敗，再寫最小實作讓它通過，保持測試全綠時重構。
- 工具安裝與純文件整理以對應檢查驗收，不為了湊 TDD 寫沒有意義的測試。
- task 真正完成並通過其驗收才勾選。stage 只完成部分時列出未完成項目，不宣稱整組完成。
- 獨立審查在新的 session 執行，審查與部署驗收是不同 stage；審查通過才進入部署驗收。
- 指定部署驗收 stage 時，檢查既有授權是否涵蓋對應環境與外部操作；已授權的範圍不重複詢問。
- 本機測試通過不等於已部署。未執行的雲端驗收保持未勾選，不自動跳過或當成通過。
- 若實作與選定 change 規格、目前技術選擇或領域定義衝突，先指出並釐清，不自行改需求。
- 不因舊 skill 提到 issue tracker 或 ADR，就自動重建舊文件流程；依目前使用者指示與 AGENTS.md 執行。
