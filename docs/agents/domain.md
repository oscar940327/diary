# Domain Docs

本專案使用單一領域語境。先讀 `CONTEXT.md` 的領域用語，再依工作閱讀以下文件：

- `docs/tech-stack.md`：目前技術選擇。
- `DISCUSSION.md`：目前方向、未決問題與下一步。
- 選定 OpenSpec change 的 proposal、specs、design 與 tasks：這次變更的需求、設計與工作。
- `openspec/specs/`：已歸檔能力的現行規格。

`docs/adr/`、`docs/archive/v1/` 與 `.scratch/` 內的舊資料是歷史參考，
只在追查舊設計或使用者明確要求時閱讀。不要求為 v2 新建 ADR 或沿用舊票；
技術選擇記在技術文件，change 的取捨記在 `design.md`。

## Layout

```text
/
|-- CONTEXT.md
|-- docs/tech-stack.md
|-- DISCUSSION.md
`-- openspec/
    |-- changes/
    `-- specs/
```

使用 `CONTEXT.md` 定義的領域用語。若工作與目前領域定義、技術選擇或選定 change 的規格衝突，
先說明差異，不自行改需求。舊 ADR 不自動成為新版限制。
