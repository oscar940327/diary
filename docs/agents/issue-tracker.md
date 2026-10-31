# Task tracking

Diary v2 直接使用 OpenSpec change 的 `tasks.md` 追蹤工作，不額外建立 Markdown tickets。

## Active workflow

- 規劃位置：`openspec/changes/<change-name>/`。
- 工作清單：該 change 的 `tasks.md`。
- 編號分組是 stage，`X.Y` 是個別 task；使用者每次指定執行哪些 stage。
- 完成且驗收通過的 task 才改成 `- [x]`，進度以 CLI 與此清單為準。
- 不另建 ticket 的 `Status:` 或第二套進度清單。

## Historical records

`.scratch/diary/` 保存舊票；`.scratch/diary-v2/` 是轉用 OpenSpec 前的早期草稿，均不作為目前工作佇列。
歷史 issue 檔曾使用 `.scratch/<feature>/issues/<NN>-<slug>.md` 與 `Status:`，需要追查時可閱讀，無須繼續更新其狀態。

舊 skill 若提到建立或讀取 ticket，先依 AGENTS.md 對照目前 change 的 tasks 與規格，不自動新增舊格式文件。
只有使用者另行要求維護歷史資料時，才在該範圍處理。
