---
name: mv-script
description: 從歌曲時間軸（timeline.json）寫 MV 或動畫短片的結構化劇本：逐項問參數、提概念方向、建立名詞表（@id 實體）與敘事、逐段寫分鏡 shots、跑 lint、用 plan-critic 做歧義審稿、渲染成文件並同步線上文件，以及下游（參考圖、試作）發現做不到時退回修改劇本。使用者提到 MV 劇本、分鏡、名詞表、glossary、shots.yaml、plan critic、劇本 lint、mv_plan 時使用。不要用在：生成關鍵幀或影片（ComfyUI、I2V）、分析音樂本身（BPM、拍點、段落、歌詞轉錄）、訓練 LoRA、剪輯後製、一般文案或與 MV 無關的文件。
---

# mv-script：MV 劇本流程（P2）

把歌曲時間軸變成可交給生成流程的結構化劇本。正本是 `plan/` 的四個 YAML；文件由腳本產生。
全部用繁體中文與使用者溝通。句子短、直接。

完整範例：`${CLAUDE_PLUGIN_ROOT}/examples/neon-courier/`（虛構的 14 鏡範例，含 timeline、plan、審稿檔與渲染產物）。不確定怎麼寫時，先看它。
新專案骨架：`${CLAUDE_PLUGIN_ROOT}/skills/mv-script/templates/`。

## 三條硬規則

1. **名詞先定義再引用**：story 與 shots 只寫 `@id`，不得用別名；每個實體寫外觀與 `not_this`。
2. **首幀與運動分開**：`first_frame` 是靜止畫面；動作只寫在 `motion`，分 `camera` 與 `subject`。
3. **每一鏡都有 `transition_in`**；逐拍的事寫成 `beat_events`，一拍一筆。

其他必守規則（細節在 [references/format.md](references/format.md)）：

- 時間用 `[小節, 拍]`；`span.to` 不含在本鏡內。
- `variation` 決定要不要末幀；外觀在鏡內會變時一定要末幀。
- 左右是觀眾視角；角色自己的左右寫 `char_left`／`char_right`。「畫面高 N%」從上緣量起。
- 每個元素寫位置、大小、面向；特寫寫聚焦部位；不准比喻；不寫看不見的東西。
- 移動或轉向的主體，`facing` 依階段寫成 dict；動作量要和時長相符。
- 不動的角色在首幀寫表情、嘴、眼。
- 每個非角色實體都要有 `refs`；定格或凍結的畫面寫 `read_as`。
- 畫面內不得有文字；字標與字卡只在後製疊。
- 精確數量標明「約」或改後製。
- 劇情與設定問使用者，精度題由 Claude 代決並記錄理由。

## 腳本

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/mv-script/scripts
python3 $S/lint_plan.py --plan plan [--timeline FILE] [--profile legacy|full] [--quiet]
python3 $S/render_plan.py --plan plan [--timeline FILE] [--labels FILE] [--out FILE]
```

依賴 python3 與 PyYAML；有 jsonschema 就用，沒有就用內建驗證器。`--plan` 必填。
新專案用 `--profile full`（預設）。lint 代碼與規則見 [references/schema.md](references/schema.md)。

## 流程

### 0. 前置：timeline

確認 `timeline.json` 符合合約（[references/timeline-contract.md](references/timeline-contract.md)）。
不符就請使用者先處理音樂分析；本外掛不分析音樂。
先用 `lint_plan.py` 讀得進去，再往下。

### 1. 參數

從 [templates/project.yaml](templates/project.yaml) 開始，複製到 `plan/`。
`params` 每一項用 AskUserQuestion **一題一題問**，不要替使用者選，也不要一次丟一整張表。
同時問**授權模式**（見下）。答案寫進 `project.yaml`。

### 2. 概念方向

提 3 個方向（每個一段：核心設定、情緒、結局），讓使用者挑一個或混合。
挑定後寫進 `decisions`（日期分段）。

### 3. 名詞表與敘事

- `glossary.yaml`：`vocab` 沿用範本；`entities` 含角色、場景、物件、特效、狀態。
  - 每個實體：`definition`、`look`、`not_this`、`aliases_forbidden`、`refs`。
  - 角色寫非對稱外觀（用 `char_left`／`char_right`）。
  - 外觀、材質、尺寸等設定上的選擇問使用者；每個實體先 `status: proposed`。
- `story.yaml`：一句話概念、每個 timeline 段落一個 beat。只寫劇情，不寫畫面。
- 寫完跑 lint。

### 4. 多鏡重複的特效先做示意

同一個特效在多鏡出現時，先做示意（靜態對照或動態），給使用者確認，**確認後才寫進 shots**。
例：「特效先閃 3 幀彩色再變單色」，看到示意後被改成「直接以單色出現」。

### 5. 逐段落

每個 timeline 段落重複：

1. **寫 shots**：一次一段，寫進 `shots.yaml`。寫完對照 [references/feasibility.md](references/feasibility.md) 的自我檢查。
2. **lint 到 FAIL 0**：WARN 逐條看；不處理的要有理由。
3. **plan-critic**：呼叫 `mv-script:plan-critic` agent（乾淨脈絡，只看檔案）。提示裡給 `plan` 目錄、`scope`（本段鏡頭範圍）與 `round`（例如 `verse_r1`）。它寫出 `plan/review/<段>_r1.yaml`。
4. **逐條標記**接受、駁回，或問使用者（格式與狀態見 [references/decisions-log.md](references/decisions-log.md)）：

   | 題目類型 | 誰決定 |
   | --- | --- |
   | 劇情、設定、角色、結局、轉場類型 | 問使用者 |
   | 尺寸、幀數、位置、時間、後製與模型分工 | Claude 代決，`resolution` 寫理由 |

   處理完給使用者看**決策表**（題號、決定、理由），不給問題清單。
5. **重跑 lint**。
6. **render**，同步線上文件，只替換變動的區塊（[references/doc-sync.md](references/doc-sync.md)）。
7. **commit 加 push**。commit 訊息寫段落與原因。劇情是否要先經使用者確認，依 `plot_review`（見下方「劇情審查時機」）：預設 `at_rough_cut` 不等確認，render 與同步後直接 commit、寫下一段；`per_section` 才要使用者確認後 commit。

### 6. 全片寫完之後

- 依概念重寫 style bible（`style_bible` 欄指向的檔案）：場景、色票、每段色調。
- 跑**一次全片 critic**（`scope` 不限），處理跨段落的矛盾與連續性。
- 重新 lint、render、同步、commit。

## 兩種授權模式

在流程第 1 步問，記在 `project.yaml` 的 `authorization`。

| 模式 | 做法 |
| --- | --- |
| `per_section`（逐段問） | 每段寫完，劇情與設定的選擇題問使用者。預設 |
| `autonomous`（使用者授權自行完成） | 劇情題由 Claude 代決，在 `decisions` 標「Claude 代決」並寫理由；鏡頭維持 `status: proposed`，留到劇情審查關卡（見下）一起檢驗；每段仍 lint、critic、commit |

授權模式下仍然要寫下每個決定。不要因為不用問，就讓決定變成隱含的。

## 劇情審查時機

「問選擇題」（授權模式）和「審寫好的劇情」是兩件事。後者在流程第 1 步問，記在 `project.yaml` 的 `plot_review`。

| 值 | 做法 |
| --- | --- |
| `at_rough_cut`（預設） | 使用者不逐段確認劇情，也不在關鍵幀前另外審。render、同步線上文件後直接 commit、寫下一段。劇情在粗剪關卡（原專案的 G3）對照 `mv_plan.md` 和影片一起檢驗；劇情問題（S）退回 P2 改劇本，再重做受影響的鏡頭 |
| `per_section` | 每段 render 後給使用者確認，確認後 commit；確認的鏡頭改 `status: confirmed` |

`at_rough_cut` 下 `status: proposed` 的意思是「劇情還沒在粗剪中檢驗過」，不是「等使用者確認」；不要在關鍵幀前提醒使用者審劇情。

## 下游發現做不到

P3（參考圖）、P4（試作）發現劇本做不到時：改 `shots.yaml`、`status` 退回 `proposed`、重跑 lint 與 critic。
流程與實例見 [references/feasibility.md](references/feasibility.md)；P2 產物怎麼銜接下游見 [references/downstream.md](references/downstream.md)。

## 參考文件

| 檔案 | 內容 |
| --- | --- |
| [references/format.md](references/format.md) | 格式與三條硬規則的完整說明 |
| [references/schema.md](references/schema.md) | 欄位表與 lint 代碼 |
| [references/timeline-contract.md](references/timeline-contract.md) | timeline.json 合約與 P1 經驗 |
| [references/decisions-log.md](references/decisions-log.md) | decisions 與 review 檔格式 |
| [references/doc-sync.md](references/doc-sync.md) | 線上文件同步 |
| [references/feasibility.md](references/feasibility.md) | 可執行性與下游退回、P4 九條教訓 |
| [references/downstream.md](references/downstream.md) | 銜接 P3、P4、P5；10 行 prompt 模板 |
| [references/g1-rubric.md](references/g1-rubric.md) | G1 animatic 審查準則（含 AutoMV 12 項分類） |
| [references/design-rationale.md](references/design-rationale.md) | 每條規則的來源與理由 |
| [references/trigger-tests.md](references/trigger-tests.md) | 觸發測試句 |
