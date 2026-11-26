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
| 實作 | 用 `openspec-apply-change`，由使用者指定本次執行的 stage。 | 指定範圍的 tasks 完成 Stage Review 並更新勾選，停在指定邊界。 |
| 獨立審查 | 在既有的 review stage 進行 Change Review。 | 阻擋問題修正、相關檢查通過，留下複查紀錄。 |
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

## Review and acceptance

| 類型 | 時機與範圍 |
| --- | --- |
| Stage Review | 在指定 Stage 的既有驗收步驟中，核對該 Stage 的 OpenSpec 驗收條件、程式變更與測試證據。 |
| Change Review | 到既有的獨立審查 Stage 時，另開新 session，用 `code-review` 分別依規格與程式規範審查整個 change。通過後才進入部署驗收。 |
| Follow-up Review | 修正後複查原 findings、直接受影響的執行路徑與相關回歸測試。若發現超出原範圍的重大風險，記錄證據，由使用者決定是否擴大審查。 |

每輪審查都記錄類型、固定的比較基準 commit、待審版本、範圍與適用的 OpenSpec 驗收條件。使用 `/review` 時提供這些資訊。有未提交修改時，記錄 `HEAD` 的 commit SHA 與當輪審查的 diff。Follow-up Review 另列原 findings、修正前與修正後的版本，以及各項驗證證據。

### 判斷與修正

- **Must Fix** 阻擋當前驗收，例如違反必要規格、可能遺失或重複保存資料、洩漏隱私，或使核心流程無法完成。**Should Fix** 有可證實的影響，可記錄理由後延後。**Optional** 是可選改善。依實際影響與當前驗收範圍分類，`P1–P4` 僅供參考。
- 每項 finding 附上檔案與行號、可觸發的情境、實際後果及判斷依據。涉及 Discord 或 Cloudflare 時，用官方資料格式或可重現的觀察核對測試。證據不足的疑慮標為待驗證。若涉及安全性、隱私、資料完整性或核心功能，先完成必要查證，或由使用者明確決定處置方式。依查證結果或明確的處置決定判定驗收，仍須符合適用的必要條件。
- 修正 Must Fix 前先查根因，檢查本次 change 內同一原因是否影響其他程式路徑，並補足必要的回歸測試。修 Bug 時優先加入能重現問題的 Regression Test，確認它因預期原因失敗，再做最小修正並重跑相關測試。若無法穩定自動重現，記錄原因與人工驗證方式。修正限於問題與直接受影響的路徑，無關重構或功能改動另行處理。

### 停止條件

- 已確認的 Must Fix 都有通過的驗證證據，相關檢查通過，涉及安全性、隱私、資料完整性或核心功能的待驗證事項已處理，且 Should Fix 與 Optional 已記錄處置，就結束本輪。Follow-up Review 結束後，Change Review 依原定 Stage 進行。
- 同一流程連續完成兩輪修正與複查後，只要仍有未解決或新發現的 Must Fix，就停止自動修正。整理共通證據，分析根因是否來自規格、外部服務假設、測試或設計，回報剩餘問題與建議處置，由使用者決定下一步。即使已達兩輪門檻，未解決的 Must Fix 仍阻擋驗收。

### Stage 完成回報

每個 Stage 完成後，以繁體中文說明主要程式流程、關鍵函式及其職責、實際測試結果，以及人工驗收的操作與預期結果。純文件工作可將程式流程與關鍵函式標為不適用。尚未執行的檢查或人工驗收標為待驗證。

## Operating rules

- 只做使用者選定的 stage；前置未完成先回報，不自行擴大到未指定的 stage。
- 有行為變更的 task 使用 TDD：確認測試因預期原因失敗，再寫最小實作讓它通過，保持測試全綠時重構。
- 工具安裝與純文件整理以對應檢查驗收，不為了湊 TDD 寫沒有意義的測試。
- task 真正完成並通過其驗收才勾選。stage 只完成部分時列出未完成項目，不宣稱整組完成。
- 指定部署驗收 stage 時，檢查既有授權是否涵蓋對應環境與外部操作；已授權的範圍不重複詢問。
- 本機測試通過不等於已部署。未執行的雲端驗收保持未勾選，不自動跳過或當成通過。
- 若實作與選定 change 規格、目前技術選擇或領域定義衝突，先指出並釐清，不自行改需求。
- 不因舊 skill 提到 issue tracker 或 ADR，就自動重建舊文件流程；依目前使用者指示與 AGENTS.md 執行。
