# mv-script

Claude Code plugin。從歌曲時間軸寫 MV／動畫短片的結構化劇本：名詞表、敘事、逐鏡分鏡；附 lint、歧義審稿與渲染。

## 這是什麼

一套 P2（概念與劇本）流程，來自一支完整 MV 的製作實作，通用化後可以給下一支影片用。

| 功能 | 內容 |
| --- | --- |
| 流程 skill | `mv-script`：問參數、提概念、建名詞表與敘事、逐段寫 shots、lint、審稿、渲染、同步文件 |
| 審稿 agent | `plan-critic`：乾淨脈絡只讀檔案，找出讀錯或要人猜的地方，寫成 `plan/review/<段>_r1.yaml` |
| 腳本 | `lint_plan.py`（引用、時間、鏡頭、寫法、敘事、結構）、`render_plan.py`（YAML 渲染成 Markdown） |
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
│   └── scripts/
│       ├── lint_plan.py
│       ├── render_plan.py
│       ├── schema_check.py
│       ├── schema/                  # JSON Schema（結構層，可替換）
│       └── words/zh-TW.yaml         # 中文詞表（可換語言）
└── tests/                           # 單元測試與 golden/example（範例的 lint 快照）
```

## 前置需求

- Claude Code。
- python3 與 PyYAML。有 `jsonschema` 套件就用它驗結構，沒有就用內建驗證器。
- 一份符合合約的 `timeline.json`，見 `skills/mv-script/references/timeline-contract.md`。

## 安裝

### 從 GitHub 安裝

```text
/plugin marketplace add alifestone/mv-script-plugin
/plugin install mv-script@mv-script-plugin
```

### 本機開發

```bash
git clone https://github.com/alifestone/mv-script-plugin.git
claude --plugin-dir ./mv-script-plugin          # 只在這個工作階段載入，不改任何設定
claude plugin validate ./mv-script-plugin       # 檢查外掛格式
python3 -m unittest discover -s mv-script-plugin/tests
```

## 使用

1. 準備 `timeline.json`。
2. 開新專案：複製 `skills/mv-script/templates/` 的 `project.yaml`、`glossary.yaml`、`story.yaml`、`shots.yaml` 到專案的 `plan/`。
3. 對 Claude 說「幫我為這首歌寫 MV 劇本」，skill 會接手流程。
4. 手動跑腳本：

```bash
S=skills/mv-script/scripts
python3 $S/lint_plan.py --plan plan --timeline analysis/timeline.json
python3 $S/render_plan.py --plan plan --out docs/mv_plan.md
```

`--plan` 必填。結束碼：lint 有 FAIL 時為 1。

範例可以直接跑：`python3 $S/lint_plan.py --plan examples/neon-courier/plan`（FAIL 0、WARN 0；OPEN 是示範用的 proposed 與 questions）。

## 跑測試

```bash
python3 -m unittest discover tests
```

範例與快照有改動時，用 `UPDATE_SNAPSHOT=1 python3 -m unittest discover tests` 重寫 `tests/golden/example/lint.txt` 與 `examples/neon-courier/docs/mv_plan.md`，再看 diff。

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
