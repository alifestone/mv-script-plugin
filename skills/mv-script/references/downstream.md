# 下游銜接：P2 產物怎麼用

P2（本外掛）的產物是 `plan/*.yaml`。這份文件說明下游各階段從哪些欄位取資料，以及 P2 要保證哪些欄位齊全。
階段名稱沿用原專案的流程（P0–P9、G0–G4）；換專案時階段名可能不同，欄位對應不變。

| 階段 | 做什麼 | 取自 P2 的欄位 |
| --- | --- | --- |
| P3 | 角色與物件、場景的參考圖，LoRA | `glossary.yaml`：`look`、`refs`、`not_this`；style bible |
| G0 | 樣張與 LoRA 審查 | 同上 |
| P4 | 8 秒端到端試作 | `shots.yaml`：選 3–4 個已通過 lint 與 critic 的鏡頭（`per_section` 時要 `confirmed`） |
| P5 | 鏡頭清單與 animatic | 全部欄位；組 prompt（見下） |
| G1 | animatic 審查 | 節奏與切點，見 [g1-rubric.md](g1-rubric.md) |
| P6–P9 | 關鍵幀、影片、修補、後製 | `first_frame`、`last_frame`、`variation`、`realize`、`beat_events`、`transition_in`、`post`、`overlay` |

## P3：參考圖

- 每個**反覆出現的非角色實體**（夥伴機器人、載具、艙體、主要場景）依 `look` 做一組固定參考圖，存 `refs/entities/<id>/`，路徑寫回該實體的 `refs`。
- 只出圖，不訓練。由使用者確認。
- P2 要保證：
  - 這類實體的 `look` 寫到可以畫出來（形狀、尺寸、顏色與色碼、材質、是否發光）。
  - `not_this` 涵蓋最可能的誤解。
  - 先在 `refs` 留位置；P3 完成後填回。
- 角色用 `refs` 指向角色表與參考圖；外觀的硬規則（例如非對稱飾品在哪一側）寫在 `look` 與 style bible，兩邊一致。
- P3 發現畫不出來：走 [feasibility.md](feasibility.md) 的退回流程。

## P4：試作

- 從已通過 lint 與 critic 的鏡頭（`per_section` 時是 `confirmed` 的鏡頭）選 3–4 鏡，要涵蓋不同路線：
  - 路線 C（視差）。
  - 路線 A 的特寫。
  - 路線 A 有非角色主體動作且含後製效果的鏡頭。
  - 若有舞蹈鏡頭（`dance_shots` > 0）再加 1 鏡。
- P2 要保證被選中的鏡頭（`per_section` 時 `status: confirmed`）`first_frame`、`last_frame`、`motion`、`model_hint` 齊全。
- 試作結果決定主模型、路線與參數；結果寫進試作報告，也決定哪些 `model_hint` 規則要改。
- 試作發現劇本問題（九條 P4 教訓）：改 `shots.yaml`，status 退回 `proposed`，重跑 lint 與 critic。

## P5：從 shots 組 prompt

P5 的 prompt 由程式從 P2 的欄位**組出來**，不是每鏡重新寫一遍。
下面用 OpenDirector 的 10 行固定標籤模板說明每一行的資料來源。這屬於 P5；P2 只要保證欄位齊全。

### 圖像（首幀）prompt：10 行固定模板

每行一個標籤，順序固定：

| 行 | 標籤 | 資料來源 | P2 要保證 |
| --- | --- | --- | --- |
| 1 | `STYLE` | style bible 的風格與色票；`project.yaml` 的 `style_bible`。由程式注入固定前綴，LLM 不得改寫（OpenDirector 的做法） | style bible 已定稿（全片鏡頭寫完後重寫） |
| 2 | `SHOT` | `shots.shot_size`，以 `vocab.shot_size` 的定義展開 | 景別有值，且與主體大小數字相容 |
| 3 | `CAMERA` | `shots.angle` 加 `first_frame` 裡的機位（離地高度、離主體距離）。**不放** `motion.camera`（那是運動，歸影片 prompt） | 機位寫在首幀；`angle` 有值 |
| 4 | `COMPOSITION` | `subjects[].placement`（x、y、depth）與 `size`；`place` 的空間配置 | 每個主體有位置與大小，錨定場景元素；數字自洽 |
| 5 | `SUBJECTS` | `subjects[]`：`ref` 展開成 glossary 的 `name` 與 `look`；加 `placement`、`size`、`facing`、`state`、遮擋關係、互動點。每個用 `@id` | 角色有 `facing` 與 `state`；表情、嘴、眼已寫；遮擋寫在 `first_frame` |
| 6 | `STATIC_ACTION` | `first_frame`（一個靜止、畫得出來的姿態）加角色 `state`。**不含**動作、轉場、前後時序、已完成的結果 | 首幀是快照，沒有動作詞（lint W1） |
| 7 | `PROPS` | `subjects` 裡 kind 為 object、vfx 的實體：glossary 的 `look`；`refs` 當參考圖。不放可讀文字、UI、logo | 非角色實體都有 `refs`；`not_this` 寫了「沒有文字」 |
| 8 | `ENVIRONMENT` | `shots.place` 對應場景的 `look`（空間、地面、天氣）與 `variants` 狀態 | 場景 `look` 完整；用的是哪個 variant 寫在鏡頭裡 |
| 9 | `LIGHTING` | 場景與實體的 `look.light`、色碼；style bible 的該段色調 | 光源位置與強弱有寫；後製光效（glow_pulse）不進這一行，進後製清單 |
| 10 | `MOOD` | `story.beats[].emotion`（該鏡 `story_beat`）加 style bible 的段落氣氛 | story beat 有 `emotion` |

規則（OpenDirector 逐字的核心）：

- `SUBJECTS` 是必填；每個被引用的主體用精確的 `@id`，並加上位置、相對大小、面向或視線、可見度與遮擋、必要時的互動點。
- `STATIC_ACTION` 只描述「一個凍結的、畫得出來的姿態」。
- `PROPS` 只列關鍵物件與固定設施。
- 不發明新角色、物件、地點、劇情事件或結果。

ViMax 的補充（P2 階段就要遵守）：每個元素寫位置，特寫寫聚焦部位，角色寫面向，不寫比喻，不寫看不見的東西。

### 影片 prompt：只寫運動

| 內容 | 資料來源 |
| --- | --- |
| 鏡頭運動 | `motion.camera`：`move`、`speed`，以 `vocab.camera_move`、`camera_speed` 的定義展開；`realize` 為 post 的不放 |
| 畫面內運動 | `motion.subject.text` 中 `realize` 含 model 的部分；用 `@id` 展開成外觀特徵代稱（例如「短髮、穿綠色洋裝的那個人在走路」） |
| 拍點事件 | `beat_events` 中由影片模型生成的項目，依 `at` 排序 |
| 末幀 | `last_frame`：`variation` 為 medium、large 時，與首幀一起餵給首尾幀模型 |
| 不放 | 後製項目（`post`、`overlay`、`realize: post` 的動作）、首幀的外觀描述（影片 prompt 不重複圖像描述） |

### 後製清單

P5 另產一份後製清單：`post`、`overlay`、`transition_in`、`beat_events` 中 `realize` 為 post 的項目。時間都用 timeline 的絕對幀號，不用鏡頭時長累加。

### 時間與幀數（通用規則）

- 切點：`round(拍點秒數 × fps)`，讀 `timeline.json`。
- 驗收看「剪輯時間軸總長等於音檔長度」，不要求每鏡生成長度剛好等於鏡頭長度。
- 影片模型每鏡頭尾多生約 0.3–0.5 秒，剪輯時裁掉。

## 退回表

審查不通過時，只退回到「能修好它的最後一步」：

| 代碼 | 問題 | 退回到 |
| --- | --- | --- |
| S | 敘事或段落概念 | **P2**（改 YAML → lint → critic → render） |
| T | 節奏或切點 | P5 或 P9 |
| K | 構圖、場景、色調 | P6（色調可能只要在 P9 調色） |
| C | 角色走樣 | P6；多鏡走樣時回 P3 |
| M | 動作或穩定性 | P7（換 seed → 改路線 → 改設計；改設計可能回 P2） |
| L | 局部瑕疵 | P8 |
| P | 畫質或流暢度 | P9 |

M 退到「改設計」時，就是 [feasibility.md](feasibility.md) 的退回流程。

## 附錄：P5 以後

### 最終剪輯要核對素材來源

- 最終剪輯（P9）要核對**每個素材檔的來源是不是選定的組合**，不能只看檔名。
- 實戰教訓：最終剪輯曾誤用測試檔。
- 做法：每次生成記錄輸入檔與輸出檔的 sha256（模型、LoRA、seed、參數）；剪輯前用清單核對每個片段的 sha256 與選定版本一致；候選與測試檔放在不進 git 的資料夾，檔名不要和選定檔相同。

### P6 以後的參考（尚未實作）

這兩項來自 ViMax，目前只記錄，等需要時再評估：

- **機位樹**：同一機位的鏡頭共用第一鏡的首幀當參考；子鏡缺什麼資訊（`missing_info`）要補。長鏡不得直接接特寫。適合場景切換少、機位反覆回用的片子；MV 場景變化多，完整的機位樹可能過重。
- **VLM 從候選圖挑選**：每個關鍵幀生 2 張以上候選，用視覺模型依「角色一致、空間一致、與文字描述相符、沒有白邊黑邊」比較。本機沒有合適的 VLM 時，改人工挑。
