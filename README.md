# mv-script

**English summary.** A Claude Code plugin for writing structured music-video (or animated short) scripts from a song timeline. It walks through project parameters, concept directions, a glossary of `@id` entities, a story layer, and a per-shot storyboard (static first frame, motion, last frame, transitions, beat events). It ships a schema-plus-semantic lint, a clean-context ambiguity critic agent, Markdown rendering, templates, and a complete fictional example in `examples/neon-courier/`. Documentation is in Traditional Chinese.

Claude Code plugin。從歌曲時間軸寫 MV／動畫短片的結構化劇本：名詞表、敘事、逐鏡分鏡；附 lint、歧義審稿與渲染。

> **Directory edition / 目錄版.** This edition contains no scripts: Claude performs the lint and rendering checks by hand from `skills/mv-script/references/manual-checks.md`. The full edition with the Python lint/render scripts and tests is on the `main` branch of [alifestone/mv-script-plugin](https://github.com/alifestone/mv-script-plugin).
>
> 這是官方目錄用的版本，不附腳本：檢查與渲染由 Claude 照 `references/manual-checks.md` 逐條做。含 Python 腳本與測試的完整版在 GitHub 的 `main` 分支。

## 這是什麼

一套 P2（概念與劇本）流程，來自一支完整 MV 的製作實作，通用化後可以給下一支影片用。

| 功能 | 內容 |
| --- | --- |
| 流程 skill | `mv-script`：問參數、提概念、建名詞表與敘事、逐段寫 shots、lint、審稿、渲染、同步文件 |
| 審稿 agent | `plan-critic`：乾淨脈絡只讀檔案，找出讀錯或要人猜的地方，寫成 `plan/review/<段>_r1.yaml` |
| 手動檢查 | `references/manual-checks.md`：Claude 逐條做的檢查表（引用、時間、鏡頭、寫法、敘事、結構）與渲染規則 |
| 範本 | `templates/`：新專案的 plan 骨架 |
| 範例 | `examples/neon-courier/`：虛構的完整範例（32 小節的歌、14 鏡），含 timeline、plan、審稿檔與渲染產物 |

本外掛**不做**：分析音樂、生成關鍵幀或影片、訓練 LoRA、剪輯後製。它只負責劇本，並說明劇本怎麼銜接這些下游（見 `skills/mv-script/references/downstream.md`）。

## 目錄結構

```text
mv-script-plugin/
├── .claude-plugin/plugin.json
├── README.md
├── agents/
│   └── plan-critic.md
├── examples/neon-courier/           # 虛構範例：analysis/、plan/、docs/mv_plan.md
├── skills/mv-script/
│   ├── SKILL.md                     # 流程（200 行內）
│   ├── references/                  # 細節：格式、欄位、合約、決定紀錄、文件同步、可執行性、下游、設計理由
│   ├── templates/                   # project / glossary / story / shots / review 骨架、labels、timeline 範例
│   └── scripts/                     # 目錄版只有資料檔，沒有程式
│       ├── schema/                  # JSON Schema（結構層，可替換）
│       └── words/zh-TW.yaml         # 中文詞表（可換語言）
```

## 前置需求

- Claude Code。
- 一份符合合約的 `timeline.json`，見 `skills/mv-script/references/timeline-contract.md`。

## 安裝

### 從官方目錄安裝

在 Claude 的目錄裡找 mv-script 安裝。

### 完整版（含腳本）

```text
/plugin marketplace add alifestone/mv-script-plugin
/plugin install mv-script@mv-script-plugin
```

## 使用

1. 準備 `timeline.json`。
2. 開新專案：複製 `skills/mv-script/templates/` 的 `project.yaml`、`glossary.yaml`、`story.yaml`、`shots.yaml` 到專案的 `plan/`。
3. 對 Claude 說「幫我為這首歌寫 MV 劇本」，skill 會接手流程。
4. 檢查與渲染：請 Claude「照 manual-checks 檢查本段」與「渲染成 docs/mv_plan.md」。

## 文件

所有細節在 `skills/mv-script/references/`：

| 檔案 | 內容 |
| --- | --- |
| `format.md` | 格式與三條硬規則 |
| `schema.md` | 欄位表與 lint 代碼 |
| `timeline-contract.md` | timeline.json 合約 |
| `decisions-log.md` | decisions 與 review 檔 |
| `doc-sync.md` | 線上文件同步 |
| `feasibility.md` | 可執行性與下游退回 |
| `downstream.md` | 銜接 P3、P4、P5 |
| `g1-rubric.md` | G1 審查準則（AutoMV 準則待補） |
| `design-rationale.md` | 每條規則的來源與理由 |
| `trigger-tests.md` | 觸發測試句 |

## 授權與來源

設計參考 AutoMV、ViMax、OpenDirector 的公開做法（見 `design-rationale.md`）；沒有複製它們的程式碼。
