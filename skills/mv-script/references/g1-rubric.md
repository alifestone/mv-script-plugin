# G1 animatic 審查準則（骨架）

G1 是 animatic（每鏡放草圖或樣張，依時間軸配原曲排好）的審查關卡。
本檔收**美學與節奏**的準則。歧義與可執行性的準則放在 `agents/plan-critic.md`。

> AutoMV 12 項準則已取得原文（2026-11-10）。歧義與可執行性類移到 plan-critic 第 13 節；美學與節奏類留在本檔，給 G1 使用。

## 審查對象與分工

| 內容 | 誰審 |
| --- | --- |
| 節奏與剪輯密度：切點是否落在拍點、密度是否符合劇本 | Claude（Sonnet） |
| 段落起伏、情緒、其他意見 | 使用者 |

審查結果用 `review.csv` 一題一列、只追加不修改；代碼 T（節奏或切點）退回 P5 或 P9，S（敘事）退回 P2。見 [downstream.md](downstream.md) 的退回表。

## 本流程已有的檢查項（不是 AutoMV 的）

| 項目 | 怎麼量 | 來源 |
| --- | --- | --- |
| 切點落在拍點 | 每個切點對 `timeline.json` 的拍點，誤差在 1 幀內 | 本流程 G1 |
| 鏡頭長度不超過上限 | 小節數不超過 `params.max_shot_bars` | lint T2 |
| 密度符合劇本 | 每段鏡頭數與 `shots.yaml` 一致 | 本流程 G1 |
| 全片覆蓋 | 剪輯時間軸總長等於音檔長度 | 本流程 P9 驗收 |
| 轉場與 `transition_in` 一致 | 實際轉場類型對 `shots.yaml` | 本外掛 |
| 拍點事件對得上 | `beat_events` 的 `at` 對上畫面變化 | 本外掛 |

## AutoMV 準則

出處：arXiv 2512.12196〈AutoMV: An Automatic Multi-Agent System for Music Video Generation〉§4.1 Evaluation metrics；定義原文見 Appendix B「Detailed Protocol of LLM and Human Experts Scoring」。
原論文：每項 1–5 整數分，各有 5 級 rubric（本檔未收錄 rubric 全文）；類別分數＝子項平均，總分＝四類加權；評審看的是成片加原曲。

| # | 類別（權重） | 準則（原文定義） | 分類 | 本流程怎麼用 |
| --- | --- | --- | --- | --- |
| 1 | Technical（20%） | Character Consistency（5%）："Stability of appearance across scenes." | 歧義與可執行性 | 移至 plan-critic 13.1（劇本層：外觀描述是否一致、glossary 是否足以讓每鏡畫成同一人） |
| 2 | Technical | Physical Authenticity（5%）："Adherence to real-world physics and natural motion." | 歧義與可執行性 | 移至 plan-critic 13.2（動作量與時長、定格與特殊物理要寫 `read_as`） |
| 3 | Technical | Lip Sync Accuracy（5%）："Alignment between mouth movement and lyrics." | 不適用 | 本流程沒有對嘴鏡頭；`params` 有對嘴鏡頭時，G1 才檢查口型對歌詞 |
| 4 | Technical | Visual Style Harmony（5%）："Color, rendering, and aesthetic consistency." | 美學 | G1：草圖與樣張的色調、渲染是否符合 style bible 每段色調；跳色的鏡頭列出 |
| 5 | Post-Production（20%） | Shot Continuity（10%）："Pacing, transitions, and temporal/spatial coherence." | 歧義與可執行性＋節奏 | 劇本層移至 plan-critic 13.3（`transition_in`、首尾銜接、空間方向）；節奏部分 G1 看切點密度與轉場是否順 |
| 6 | Post-Production | Audio–Visual Correlation（10%）："Alignment between visuals and musical rhythm/emotion." | 歧義與可執行性＋節奏 | 劇本層移至 plan-critic 13.4（`beat_events` 對拍、動作與拍點間距）；G1 看畫面能量是否跟段落能量起伏 |
| 7 | Content（30%） | Musical Theme Relevance（10%）："Alignment of the visuals with the song's meaning." | 歧義與可執行性 | 移至 plan-critic 13.5（story 每段 `lyric_link` 是否寫清楚歌詞與畫面的對應） |
| 8 | Content | Storytelling（10%）："Narrative structure and character coherence." | 美學（敘事） | G1：使用者看段落起伏、角色動機是否看得懂 |
| 9 | Content | Emotional Expression（10%）："Clarity and depth of emotional portrayal." | 美學 | G1：每段 `emotion` 是否在畫面上讀得出來（表情、色調、運鏡） |
| 10 | Art（30%） | Visual Composition & Quality（10%）："Lighting, framing, and overall fidelity." | 美學 | G1：構圖、光線、景別變化；畫質留到 G3／G4 |
| 11 | Art | Creativity（10%）："Novelty of concepts, scenes, and transitions." | 美學 | G1：使用者意見，不由 Claude 評分 |
| 12 | Art | AI Novelty（10%）："Meaningful integration of AI-native aesthetics." | 美學 | G1：使用者意見，不由 Claude 評分 |

美學類（4、8–12）是參考準則，不打分、不產生必答題；Claude 只在 G1 列出觀察，由使用者決定。

### 已知的研究結論（不是準則條目）

這是研究報告裡有原文依據的結論，列在這裡只是備忘，不代表它對應 12 項中的哪一項：

- AutoMV 的消融實驗：拿掉角色庫，角色一致性分數從 3.07 掉到 1.22（整體專家分數從 2.42 降到 1.84）。拿掉 verifier，整體專家分數從 2.42 降到 2.08。
- AutoMV 自己列出的缺點：手物接觸等物理錯誤、動作不跟拍、畫面文字亂碼。

## 補上準則時的流程

1. 取得 12 項原文，原樣貼進「準則（原文）」欄，標明出處。
2. 逐項分類。
3. 屬於美學與節奏的：寫「G1 怎麼用」（量什麼、怎麼判定通過）。
4. 屬於歧義與可執行性的：移到 `agents/plan-critic.md` 的「13. AutoMV 準則」，本表該列標「移至 plan-critic」。
5. 更新 `design-rationale.md`：每項準則一列，來源標 AutoMV。
