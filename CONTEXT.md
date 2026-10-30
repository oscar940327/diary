# Diary

Diary 是供擁有者長期保存、查閱與運用私人生活紀錄的系統。
這份文件只定義領域用語；架構、功能範圍與實作細節分別記在 ADR、規格與 Tickets。

## Language

**Entry**:
一次提交形成的獨立紀錄，具有穩定身分。同一天可以有多筆 Entry。
_Avoid_: 每日文件、日記頁

**Entry Time**:
擁有者指定這筆 Entry 所屬的日期與時間，用來表達事情發生或應歸屬的時刻，
與系統收到紀錄的建立時間不同。
_Avoid_: 建立時間

**Original Content**:
擁有者親自輸入的完整原文，與任何 AI 衍生內容分開。
_Avoid_: AI 摘要、AI 輸入

**Entry Revision**:
某筆 Entry 的一個不可覆寫的原文版本。不同版本仍屬於同一筆 Entry。
_Avoid_: 備份、AI Draft

**AI Draft**:
AI 根據特定 Entry Revision 產生的摘要或結構化解讀提案，不能代替 Original Content。
_Avoid_: 原文、最終事實

**AI Correction**:
擁有者對 AI Draft 的人工修正，獨立於原文與 AI 產生的提案。
_Avoid_: Original Content、AI Draft

**Insight Agent**:
檢索 Original Content 並據此回答個人歷史問題的助理，與執行提醒或其他外部行動的能力不同。
_Avoid_: 搜尋框、提醒機器人

**Conversation**:
與 Insight Agent 的持續多輪對話。過往回答可提供對話脈絡，但不構成個人經歷的證據。
_Avoid_: Entry、證據來源
