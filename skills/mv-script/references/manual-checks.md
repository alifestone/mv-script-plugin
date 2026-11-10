# 手動檢查（目錄版）

目錄版不附腳本。原本由 `lint_plan.py` 與 `render_plan.py` 做的事，改由 Claude 照本檔逐條做。
完整版（含腳本與測試）在 GitHub：`/plugin marketplace add alifestone/mv-script-plugin`，再 `/plugin install mv-script@mv-script-plugin`。

參考文件裡寫「跑 lint」「lint 到 FAIL 0」「render」的地方，在目錄版一律照本檔做。

## 怎麼做

1. 讀 `plan/` 的四個 YAML、`review/*.yaml`，以及 `project.yaml` 的 `timeline` 指向的 timeline.json。
2. 照下面的表逐條檢查。每一條都要實際對照檔案，不憑印象判斷。
3. 結果照完整版的格式列出，每行一筆：`層級 代碼 位置: 訊息`。最後一行寫 `FAIL n  WARN n  OPEN n`。
4. 有 FAIL 就修到 0 再往下。WARN 逐條看；不處理的要寫理由。
5. 範圍大時，一段一段做（例如只查本段鏡頭，加上前後各一鏡的銜接）。

詞表在 `scripts/words/zh-TW.yaml`。結構規則在 `scripts/schema/*.schema.json`。可用的值在 `glossary.yaml` 的 `vocab`。

## 檢查表

### 結構（X1，FAIL）

對照 `scripts/schema/{project,glossary,story,shots}.schema.json`：必填欄位、型別、列舉值（例如 `status`、`variation`、`route`、`realize`、`kind`）。

### 名詞表（G）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| G1 | FAIL | 每個實體都有 `kind`、`name`、`status`、`definition`。`kind` 只能是 character、place、object、vfx、state |
| G2 | WARN | 非角色實體沒有 `look`；角色沒有 `look`，也沒有 `refs` |

### 引用（R）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| R1 | FAIL | story 與 shots 裡每個 `@id` 都在 glossary |
| R2 | FAIL | 出現某實體的 `aliases_forbidden`（清單本身除外），或出現 `decisions.banned_motifs` 的母題 |
| R3 | WARN | story 與 shots 直接寫了實體名稱（去掉括號內的部分，2 字以上），應改成 `@id` |

### 敘事（N）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| N1 | FAIL | timeline 的每個段落在 story 都有一個 beat |
| N2 | FAIL | beat 有 `id`、`section`、`bars`、`story`、`emotion`、`lyric_link`、`status`；`bars` 等於 timeline 段落的 `[bar_start, bar_end]` |
| N3 | WARN | 敘事層混入鏡頭用語（詞表 `story_camera_words`，例如特寫、鏡頭、畫面左） |

### 鏡頭（S）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| S1 | FAIL | 每鏡有 `id`、`section`、`story_beat`、`span`、`place`、`shot_size`、`angle`、`route`、`variation`、`subjects`、`first_frame`、`motion`、`transition_in`、`status` |
| S2 | FAIL | `shot_size`、`angle`、`variation` 的值在 vocab；`route` 是 A、B、C；`story_beat` 存在於 story；`lyrics` 的 id 存在於 timeline |
| S3 | FAIL | 每個 subject 有 `ref`、`placement`、`size`；`placement.x／y／depth` 的值在 vocab 的 `screen_x／screen_y／depth`；角色另外要有 `facing` 與 `state`。`facing` 可以是單一值，也可以是依階段的 dict，每個值都要在 `vocab.facing` |
| S4 | FAIL | `motion.camera.move`、`speed` 的值在 vocab；`realize` 是 model、post、model+post、none；`variation` 為 medium 或 large 時必須有 `last_frame` |
| S5 | FAIL | `transition_in.type` 的值在 vocab；flash_white 要有 `frames`；whiteout 要有 `in_beats` 與 `out_beats`；fade、dissolve 要有 `beats` 或 `frames`；match_cut 要在 `note` 寫明對齊的是什麼 |
| S6 | FAIL | route C 不超過 1 小節、不用於 ECU／CU、主體動作只能 `realize: post` |
| S7 | WARN | first_frame、last_frame、motion、beat_events 寫到的 `@id`，都列在 subjects 或 place |

### 時間（T）

時間位置換算：`[小節, 拍]` 對照 timeline 的 `beats`（`bar`、`beat_in_bar`），拍可以寫小數。

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| T1 | FAIL | `span.from`、`span.to` 是 timeline 裡存在的拍點，而且 `to` 晚於 `from` |
| T2 | FAIL | 一鏡的長度不超過 `params.max_shot_bars` 小節（預設 2） |
| T3 | FAIL | 第一鏡從 `[0, 0]` 開始；每鏡的 `span.from` 等於上一鏡的 `span.to` |
| T4 | FAIL | 鏡頭起點的小節落在它的 `section` 範圍內 |
| T5 | FAIL | 每筆 beat_event 有 `event`，`at` 是合法拍點，而且在本鏡時間內 |
| T6 | INFO | 鏡頭總共覆蓋到幾秒，對照全曲長度 |

### 寫法（W、Y）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| W1 | WARN | first_frame 出現動作詞（詞表 `motion_words`，例如正在、開始、轉向）。首幀必須是靜止畫面 |
| W2 | WARN | 模糊詞（詞表 `vague_words`，例如一些、適度、感覺） |
| W3 | WARN | 「閃三次」這類序列（詞表 `seq_re`）沒有拆成 beat_events |
| Y1 | FAIL | YAML 值裡有「空格＋#」卻沒加引號，# 之後會被當成註解吃掉 |

### 新規則（V、F）

| 代碼 | 層級 | 檢查 |
| --- | --- | --- |
| V1 | WARN | ECU／CU 鏡頭的 first_frame 沒寫聚焦部位（詞表 `focus_parts`） |
| V2 | WARN | story 與 shots 出現比喻詞（詞表 `metaphor_words`，排除 `metaphor_exclude` 的複合詞） |
| F1 | WARN | subject 的 `state` 含「→」，或 motion.subject 寫了外觀變化（詞表 `appearance_change`，先排除 `appearance_exclude`），卻沒有 `last_frame`。眨眼（同一子句裡同時有閉和睜）不算 |
| F2 | WARN | motion.subject 對某主體寫了轉向（`turn_words`）或水平行進（`travel_words`），但它的 `facing` 是單一值，沒有依階段寫。垂直移動不算；轉的是視線、光帶這類部位（`part_words`）也不算 |
| F3 | INFO | route A、景別 ECU／CU／MCU／MS、角色在本鏡沒有動作時，first_frame 要寫表情、嘴、眼（詞表 `face_state`）。`facing: away` 與 `no_face: true` 免檢 |
| F4 | WARN | 同一鏡相鄰兩筆 beat_events 相隔不到 1 拍，後一筆卻寫了轉向、行進或垂直位移。「上升中」這類狀態描述不算 |

### 待確認（OPEN）

| 代碼 | 檢查 |
| --- | --- |
| P1 | 列出所有 `status: proposed` 的實體、beat、鏡頭 |
| Q1 | 列出所有 `questions` |
| Q2 | 列出 `review/*.yaml` 裡 `status: open` 的題目 |

## 渲染（取代 render_plan.py）

照 `examples/neon-courier/docs/mv_plan.md` 的版面寫 `docs/mv_plan.md`：

- `@id` 換成名詞表的名稱，用粗體。
- 時間位置換成秒數，格式是 `分:秒.十分位`。
- 欄位名稱照 `plan/labels.yaml` 的 `fields` 翻成中文；沒有對應的就顯示原 key。
- 產物檔頭照 `labels.yaml` 的 `texts`。沒有的話寫明「本檔由 plan/ 產生，不要手改」。
- 這份 Markdown 是產物。要改就改 `plan/`，再重新產生。
