# 劇本格式（plan/）

`plan/` 的 YAML 是劇本正本。`docs/mv_plan.md` 與線上文件都由 `render_plan.py` 產生，不手改。
格式與歌曲無關，下一支影片沿用同一套結構，只換內容。欄位表見 [schema.md](schema.md)。

## 四個檔案的分工

| 檔案 | 層級 | 內容 |
| --- | --- | --- |
| `project.yaml` | 參數 | 敘事類型、歌詞對應方式、角色與道具限制等；每支影片開頭由使用者選；`decisions` 記錄已確認的方向 |
| `glossary.yaml` | 名詞 | 詞彙（景別、轉場、後製效果、方向）加實體（角色、場景、物件、特效、狀態） |
| `story.yaml` | 敘事 | 一句話概念、每段落發生什麼；只寫劇情與情緒，不寫畫面細節 |
| `shots.yaml` | 鏡頭 | 每一鏡的時間、主體位置、首幀、運動、末幀、轉場、拍點事件、後製 |

審稿紀錄放 `plan/review/<段落>_r<輪>.yaml`，格式見 [decisions-log.md](decisions-log.md)。

## 三條硬規則

1. **名詞先定義再引用**。story 與 shots 裡的角色、場景、物件、特效一律寫 `@id`，不得用別名。
   每個實體在 glossary 寫清楚外觀（形狀、大小、顏色、材質、是否發光）與「不是什麼」（`not_this`）。
2. **首幀與運動分開**。`first_frame` 是一張靜止畫面，不寫正在進行的動作。
   動作只寫在 `motion`，並分成 `camera`（鏡頭怎麼動）與 `subject`（畫面裡的東西怎麼動）。
3. **每一鏡都要有 `transition_in`**。類型只能用 `vocab.transition` 的值。
   需要逐拍發生的事（倒數、閃動）寫成 `beat_events`，一拍一筆，不寫「閃三次」。

## 時間位置

- 位置寫成 `[小節, 拍]`，拍從 1 起算，可寫小數。`2.5` 是第 2 拍後半，在相鄰兩拍之間線性內插。
- `[0, 0]` 是歌曲開頭。弱起的拍算 bar 0（例如 `[0, 4]`）。
- `span.to` 不含在本鏡內，等於下一鏡的 `span.from`。
- 全片最後一鏡的 `span.to` 可以寫 `end`。
- 不規則小節（3 拍、5 拍）照 `timeline.json`，不要自己補拍。
- 切點最終落在絕對幀號：`frame = round(t × fps)`，由下游讀 timeline，劇本裡不寫幀號。
- 人聲落點（「3、2、1」、英文 hook）以量測值寫在 `beat_events.sync`，例如 `人聲「啟」約 8.30 s`。量法見 [timeline-contract.md](timeline-contract.md)。

## 首幀、末幀

- `first_frame` 是本鏡第一個完整畫面，不含轉場效果。淡入、閃白都疊在它上面。
- `last_frame` 是本鏡最後一個完整畫面。
- 兩者都是靜止畫面，只寫「此刻看起來怎樣」。
  - 不行：「他即將站起來」。
  - 可以：「他坐在椅子上，身體微微前傾」。
- `last_frame` 必須等於 `first_frame` 加上 `motion` 的結果：motion 裡每個動作都要在末幀看得到。
- `variation` 決定要不要寫末幀（借自 ViMax）：

| variation | 意思 | 末幀 |
| --- | --- | --- |
| small | 首尾幀幾乎相同（呼吸、眨眼、輕微浮動） | 可不寫，只用首幀生成 |
| medium | 主體狀態或位置明顯改變，構圖不變 | 必須寫，用首尾幀生成 |
| large | 構圖、景別或主體大幅改變 | 必須寫，考慮拆成兩鏡 |

- 例外：角色外觀在一鏡內會變（睜眼、表情變化）時，不論 variation 都要寫 `last_frame`。不寫的話，瞳孔顏色之類的細節會漂掉。

## 方向與尺寸

- 畫面上的左右一律是**觀眾看到的左右**：`screen_left`、`screen_right`。
- 指角色自己的左右時寫 `char_left`、`char_right`，例如「反光條在 `char_left` 袖口」。
- `facing` 值：`to_camera`、`three_quarter_left/right`、`profile_left/right`、`away`。
  `profile_left` 是正側面、鼻尖指向畫面左。
- 「畫面高約 N%」一律從畫面**上緣**往下量：0% 是上緣，100% 是下緣。
- 「畫面寬約 N%」量的是寬度，或從畫面左緣起算的位置，依句意；寫成位置時要寫「從左緣起算」。
- 位置優先錨定場景元素，例如「在 @booth 的正中央」，百分比座標只當輔助。
- 同一主體的位置、大小數字要彼此相容。「高為畫面 1/4、頂端在 70%」又要「底座在地面圓心」會互相矛盾。
- 精確數量（剛好 12 扇窗）生成模型做不到：寫「約」並接受近似，或改成 `realize: post`。

## facing 依階段寫成 dict

主體在一鏡內移動或轉向時，`facing` 不能只寫一個值。依階段寫成 dict，階段名自訂，值取自 `vocab.facing`：

```yaml
facing: {entering: profile_left, settled: to_camera}
state: "[2,2] 從畫面右緣外滑入，減速時原地轉向，[2,3] 停穩時正面朝鏡頭"
```

- 靜止的主體寫單一值。
- 階段轉換的時間點寫在 `state` 或 `motion.subject.text`，並對應到 `beat_events`。

## 動作量與時長

- 兩個 `beat_events` 之間的動作量要和時長相符。明顯的位移或轉身至少約 1 拍。
- 不到 1 拍就要完成位移與轉身，生成模型做不到，後製只能加速到動作很急。
- 保持不動的角色要在 `first_frame` 寫明表情、嘴巴開合、眼睛開閉；沒寫的話模型會自己選（例如嘴巴微張）。lint F3 只做提醒（INFO），只查 ECU、CU、MCU、MS 景別，critic 做最終判斷（`facing: away` 的主體、實體寫了 `no_face: true` 的免檢）。

## status 與 questions

| 欄位 | 意思 |
| --- | --- |
| `status: proposed` | Claude 提案，待使用者確認 |
| `status: confirmed` | 使用者確認 |
| `questions: [...]` | 還沒回答的問題 |

- 每個實體、每個 story beat、每一鏡都有 `status`。
- 生命週期：Claude 寫入 `proposed`；問題放 `questions`；使用者回答後移除該問題；整段使用者確認後改 `confirmed`。
- 授權 Claude 自行完成時，鏡頭維持 `proposed`，等重審關卡再確認（見 SKILL.md）。
- `lint_plan.py` 會把 `proposed` 與 `questions` 全部列為 OPEN，不算 FAIL。

## transition_in 與 beat_events

- `transition_in` 寫在**進入本鏡**的那一鏡。寫法：`{type: flash_white, frames: 2}`。
  - 有參數的類型：`flash_white` 要 `frames`；`whiteout` 要 `in_beats`、`out_beats`；`fade_from_black`、`fade_to_black`、`dissolve` 要 `beats` 或 `frames`。
  - `match_cut` 必須在 `note` 寫出前後兩鏡對齊的是什麼。
- `beat_events`：`at` 必須落在本鏡時間內（含起點、不含終點）；`event` 必填；`sync` 寫對應的聲音。
  - 序列拆開：「3、2、1」寫成 3 筆，各自一個 `at`。
  - 數量寫逐筆，不寫「閃三次」。

## 畫面內不得有文字

- 模型畫不出可讀的文字。看板、螢幕、牆面、艙體一律寫成抽象色塊、圖案或影像。
- 字標與字卡只在後製疊，寫在 `overlay`（`{zone, content}`）。
- 實體的 `not_this` 要寫「上面沒有文字、數字、logo」。
- 由 `params.brand_text: post_only` 控制，lint 與 critic 都會檢查。

## 選填欄位

| 欄位 | 用途 |
| --- | --- |
| `read_as` | 觀眾應該把這個畫面看成什麼。例：一個定格在半空的杯子，生成出來看起來像漂浮，要寫 `read_as: 杯子被定格，不是漂浮` 並補足讓人看出凍結的線索（水花也停在半空） |
| `model_hint` | 建議的生成路線。寫通用規則，模型名稱只當例子；規則見 [feasibility.md](feasibility.md) |
| `notes` | 分工、連續性、下一鏡接點 |
| `questions` | 還沒回答的問題 |

## 流程

```text
project.yaml → glossary.yaml → story.yaml → shots.yaml
  → lint_plan.py          # 程式檢查（引用、別名、轉場、時間覆蓋、必填欄位、模糊詞、新規則）
  → plan-critic           # 歧義審稿（乾淨脈絡，只讀檔案）→ review/<段落>_r1.yaml
  → 分流處理、重跑 lint
  → render_plan.py        # 產生 docs/mv_plan.md；同步線上文件
```
