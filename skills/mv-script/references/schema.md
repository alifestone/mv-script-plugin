# 欄位表（schema）

欄位以 `examples/neon-courier/plan/` 的實際檔案為準。結構由 `scripts/schema/*.schema.json` 管，語意由 `lint_plan.py` 管。

## 兩層檢查

| 層 | 管什麼 | 誰管 | 可否替換 |
| --- | --- | --- | --- |
| 結構 | 必填欄位、型別、列舉（`status`、`route`、`variation`、`realize`、`kind`） | `schema/*.schema.json`，lint 代碼 X1（FAIL） | 可以。換掉 schema 目錄即可（`--schema DIR`），沒有 jsonschema 套件時用內建驗證器 |
| 語意 | 詞彙值在 `vocab` 裡、`@id` 存在、時間落在拍點、末幀、轉場參數、寫法規則 | `lint_plan.py` 與 `words/zh-TW.yaml` | 規則跟著流程走；詞表可換語言（`--words FILE`） |

- JSON Schema 的物件都是開放的：多寫的欄位不會 FAIL，但 lint 與 render 不認得它。
- 選填欄位（`read_as`、`model_hint` 等）目前不在 schema 的 `properties` 裡，由 lint／critic 以文字規則檢查。
- 詞彙值（`shot_size`、`angle`、`camera_move`、`transition`…）在 schema 只要求是字串；是否在 `vocab` 內由 lint S2–S5 管。

## project.yaml

| 欄位 | 必填 | 型別／可選值 | 說明 |
| --- | --- | --- | --- |
| `schema_version` | 是 | 整數 | 目前是 1 |
| `title` | 是 | 字串 | 影片名稱 |
| `timeline` | 否 | 路徑 | `timeline.json`，相對於 plan 目錄的上一層；可被 `--timeline` 蓋掉 |
| `lyrics`、`character_refs`、`style_bible` | 否 | 路徑 | 歌詞檔、角色參考圖資料夾、風格規範 |
| `params.narrative_type` | 否 | `story`／`performance`／`mixed`／`abstract` | 敘事類型 |
| `params.lyric_mapping` | 否 | `section`／`line`／`literal` | 段落層對應、每句有畫面、字面照畫 |
| `params.dance_shots` | 否 | 整數 | 舞蹈英雄鏡頭數；0 不跳舞 |
| `params.lip_sync` | 否 | 布林 | 是否對嘴 |
| `params.second_characters` | 否 | `{allowed: [non_human, designed_human], extras_count_as_character: bool}` | 第二角色限制 |
| `params.props_in_hand` | 否 | `allowed`／`brief_only`／`forbidden` | 手持道具 |
| `params.scene_limit` | 否 | 整數或 null | 場景數上限；null 不設限 |
| `params.max_shot_bars` | 否 | 整數（預設 2） | 一般鏡頭長度上限（小節）；lint T2 |
| `params.brand_text` | 否 | 字串，例 `post_only` | 畫面內文字政策 |
| `params.brand_appears_if` | 否 | 字串，例 `story_relevant` | 字標出現條件 |
| `decisions` | 否 | 物件 | 使用者確認的方向，見 [decisions-log.md](decisions-log.md)；`banned_motifs` 是字串陣列，lint R2 掃全文 |
| `authorization`、`docs` | 否 | 見 templates/project.yaml | 外掛流程自己用：授權模式與線上文件 id，見 [doc-sync.md](doc-sync.md) |

## glossary.yaml

頂層：`vocab`（必填）、`entities`（必填）。

### vocab

| 鍵 | 必填 | 型別 | 內容 |
| --- | --- | --- | --- |
| `shot_size` | 是 | 物件 `{值: 說明}` | ECU、CU、MCU、MS、MLS、FS、LS、ELS、INSERT |
| `angle` | 是 | 物件 | eye、low、high、top、dutch |
| `camera_move` | 是 | 物件 | static、push_in、pull_out、pan_left/right、tilt_up/down、track、crane_up/down、orbit_left/right |
| `camera_speed` | 是 | 物件 | slow、medium、fast（以畫面變化量定義） |
| `variation` | 是 | 物件 | small、medium、large |
| `transition` | 是 | 物件 | cut、cut_on_action、match_cut、flash_white、whiteout、fade_from_black、fade_to_black、dissolve |
| `post_effect` | 否 | 物件 | flash_frames、glow_pulse、shake、chromatic、speed_ramp、freeze |
| `screen_x` | 是 | 陣列 | screen_left、center_left、center、center_right、screen_right（觀眾視角五等分） |
| `screen_y` | 是 | 陣列 | top、upper、middle、lower、bottom |
| `depth` | 是 | 陣列 | fg、mg、bg |
| `facing` | 否 | 陣列 | to_camera、three_quarter_left/right、profile_left/right、away |

vocab 是通用的，直接沿用 [templates/glossary.yaml](../templates/glossary.yaml) 的內容；要增補值就在這裡加，不要在鏡頭裡自創。

### entities.<id>

id 是小寫英文、數字、底線（`[a-z_][a-z0-9_]*`），劇本裡寫 `@id`。

| 欄位 | 必填 | 型別／可選值 | 說明 |
| --- | --- | --- | --- |
| `kind` | 是 | `character`／`place`／`object`／`vfx`／`state` | 角色、場景、物件、特效、狀態 |
| `name` | 是 | 字串 | 顯示名稱；劇本裡不准寫（lint R3 警告） |
| `status` | 是 | `proposed`／`confirmed` | 見 format.md |
| `definition` | 是 | 字串 | 一句話：是什麼、在劇情裡做什麼 |
| `look` | 非角色建議必填 | 物件，子欄位自訂 | 外觀：shape、size、color、light、material、motion、state…；沒有會 WARN（G2） |
| `refs` | 否 | 陣列或字串 | 參考圖路徑。每個非角色實體都應有，只靠文字畫不出來 |
| `not_this` | 否 | 字串陣列 | 最可能的誤解，每條一個 |
| `aliases_forbidden` | 否 | 字串陣列 | 禁用別名；出現在 story 或 shots 會 FAIL（R2） |
| `questions` | 否 | 字串陣列 | 還沒回答的問題 |
| `no_face` | 否 | 布林 | `true`＝這個角色沒有臉（機器人、剪影），lint F3 免檢 |
| `variants`、`role`、`plot_functions`、`extras`、`notes` | 否 | 自由 | 場景的狀態版本、劇情身分、劇情功能、路人規則、備註 |

寫外觀的慣例：
- 非對稱外觀要明寫，用 `char_left`／`char_right`。
- 數字要有單位與基準（公尺、畫面高 %）。
- 色碼值含 `#` 時整個值加引號，否則 YAML 會當成註解（lint Y1）。

## story.yaml

| 欄位 | 必填 | 型別 | 說明 |
| --- | --- | --- | --- |
| `logline`、`theme`、`tone`、`ending` | 否 | 字串 | 一句話概念、主題、氣氛、結局 |
| `status` | 否 | `proposed`／`confirmed` | 整份敘事的狀態 |
| `questions` | 否 | 陣列 | |
| `beats[]` | 是 | 陣列 | 每個 timeline 段落至少一筆（lint N1） |
| `beats[].id` | 是 | 字串 | 鏡頭的 `story_beat` 指向它 |
| `beats[].section` | 是 | 字串 | 必須是 `timeline.sections[].label` |
| `beats[].bars` | 是 | `[bar_start, bar_end]` | 必須等於 timeline 該段（lint N2） |
| `beats[].places` | 否 | `@id` 陣列 | |
| `beats[].story` | 是 | 字串 | 只寫劇情；混入鏡頭用語會 WARN（N3） |
| `beats[].emotion`、`beats[].lyric_link` | 是 | 字串 | 情緒走向、歌詞與劇情的對應 |
| `beats[].status` | 是 | `proposed`／`confirmed` | |

## shots.yaml

頂層：`shots`（陣列，必填）。

### shot

| 欄位 | 必填 | 型別／可選值 | 說明 |
| --- | --- | --- | --- |
| `id` | 是 | 字串 | `s001`…，補零到 3 位 |
| `section` | 是 | 字串 | timeline 段落 label；起點 bar 要在段內（T4） |
| `story_beat` | 是 | 字串 | story beat 的 id（S2） |
| `span` | 是 | `{from, to}`，各為 `[小節, 拍]` 或 `end` | 首尾相接（T3）；第一鏡從 `[0, 0]`；不超過 `max_shot_bars`（T2） |
| `lyrics` | 否 | 歌詞 id 陣列 | 必須在 `timeline.lyrics[].id`（S2） |
| `place` | 是 | `"@id"` | 場景 |
| `shot_size` | 是 | `vocab.shot_size` | S2 |
| `angle` | 是 | `vocab.angle` | S2 |
| `route` | 是 | `A`／`B`／`C` | A 一般 I2V；B 指定動作（姿勢控制）；C 靜態圖加視差 |
| `variation` | 是 | `small`／`medium`／`large` | medium、large 必須有 `last_frame`（S4） |
| `subjects` | 是 | 陣列 | 見下表 |
| `first_frame` | 是 | 字串 | 靜止畫面；動作詞會 WARN（W1） |
| `motion.camera` | 是 | `{move, speed, realize, note?}` | `move`、`speed` 取自 vocab；`realize` 是 `model`／`post`／`model+post`／`none` |
| `motion.subject` | 是 | `{text, realize}` | `realize` 同上 |
| `last_frame` | 條件 | 字串或 null | small 可為 null |
| `beat_events` | 否 | `[{at, sync?, event}]` | `at` 在本鏡內（T5） |
| `transition_in` | 是 | `{type, frames?, beats?, in_beats?, out_beats?, note?}` | `type` 取自 `vocab.transition`（S5）；各類型的必填參數見 format.md |
| `post` | 否 | 陣列 | 後製項目，如 `{effect: glow_pulse, at: [1, 1], frames: 4}`；`effect` 取自 `vocab.post_effect` |
| `overlay` | 否 | `{zone, content}` 或 null | 字標與字卡 |
| `status` | 是 | `proposed`／`confirmed` | |
| `notes`、`questions` | 否 | 字串、陣列 | |
| `read_as` | 否 | 字串 | 觀眾應看成什麼，見 format.md |
| `model_hint` | 否 | 字串 | 建議生成路線，見 [feasibility.md](feasibility.md) |

route 限制（lint S6）：C 鏡頭不超過 1 小節、不用於特寫（ECU／CU）、主體動作只能 `realize: post`。

### shot.subjects[]

| 欄位 | 必填 | 型別／可選值 | 說明 |
| --- | --- | --- | --- |
| `ref` | 是 | `"@id"` | |
| `placement` | 是 | `{x, y, depth}` | 取自 `vocab.screen_x`、`screen_y`、`depth`（S3） |
| `size` | 是 | 字串 | 大小與位置的數字，錨定場景元素 |
| `facing` | 角色必填 | `vocab.facing` 值，或依階段的 dict | 移動或轉向時用 dict（F2） |
| `state` | 角色必填 | 字串或 dict | 此刻狀態；寫了 `→` 代表有變化，要有 `last_frame`（F1） |

畫面裡寫到的實體要列在 `subjects` 或 `place`，才有位置與大小（S7 警告）。

## review/<段落>_r<輪>.yaml

| 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `round` | 是 | 例如 `intro_r1` |
| `issues[].id` | 是 | `Q01`… |
| `issues[].where` | 是 | `shots.s003.motion.subject` |
| `issues[].category` | 否 | critic 檢查清單編號 |
| `issues[].quote` | 是 | 原文逐字 |
| `issues[].problem`、`question` | 是 | |
| `issues[].options` | 否 | 2–4 個候選答案 |
| `issues[].severity` | 是 | `high`／`medium`／`low` |
| `issues[].status` | 是 | `open`／`resolved` |
| `issues[].resolution` | resolved 必填 | 怎麼處理與理由 |
| `issues[].decided_by` | 否 | `claude`／`user` |

詳見 [decisions-log.md](decisions-log.md)。

## lint 代碼總表

| 代碼 | 層級 | 內容 |
| --- | --- | --- |
| G1、G2 | FAIL、WARN | 實體必填欄位；非角色缺 `look` |
| R1、R2、R3 | FAIL、FAIL、WARN | `@id` 不存在；禁用別名或禁用母題；寫了名稱沒寫 `@id` |
| T1–T5 | FAIL | 拍點存在；長度上限；首尾相接；段落範圍；beat_events 在鏡內 |
| S1–S7 | FAIL（S7 WARN） | 必填欄位；詞彙值；主體；運動；轉場；route 限制；subjects 漏列 |
| W1–W3 | WARN | 首幀有動作詞；模糊詞；序列沒拆 |
| N1–N3 | FAIL、FAIL、WARN | 段落沒敘事；beats 欄位與 bars；敘事混入鏡頭用語 |
| Y1 | FAIL | 值裡的 ` #` 被當成註解 |
| X1 | FAIL | 不符 schema（只在 `full`） |
| V1 | WARN | 特寫的首幀沒寫聚焦部位 |
| V2 | WARN | 比喻詞 |
| F1 | WARN | 外觀會變卻沒有 `last_frame`（眨眼，即同一子句有「閉」又有「睜」，不報） |
| F2 | WARN | 轉向或水平行進（滑入、走向、衝出…）的主體 `facing` 是單一值；上升、下降等垂直移動不算 |
| F3 | INFO | 靜止角色的首幀沒寫表情、嘴、眼（只提醒，由 critic 判斷）；只查 ECU、CU、MCU、MS 景別，`facing: away`、實體 `no_face: true` 免檢 |
| F4 | WARN | 相鄰拍點不到 1 拍卻含位移 |

OPEN 項目（非失敗）：`status: proposed`、`questions`、review 裡 `status: open`。
