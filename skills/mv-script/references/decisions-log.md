# 決定紀錄與審稿檔

兩個地方記決定：`project.yaml` 的 `decisions`（方向），`plan/review/<段落>_r<輪>.yaml`（逐題）。
原則：沒有隱含的決定。每個選擇都寫下來，使用者看得到、之後查得到。

## project.yaml 的 decisions

### 寫法

- 依日期分段。每段一行註解 `# YYYY-MM-DD 段落或事件`，下面是這一天的決定。
- 每列 `key: value`，後面加中文註解說明（`#` 前至少兩個空格）。
- key 用小寫英文與底線；value 用短的列舉值；細節寫在註解。
- 使用者原話的重點放註解，不要改寫成別的意思。

```yaml
decisions:
  # 2026-03-02 概念
  concept: rainy_night_delivery        # 使用者從 3 個方向挑「雨夜送信」
  banned_motifs: [幽靈]                # 禁用母題；lint 掃全文
  # 2026-03-04 Chorus
  chase_route: alley_to_footbridge     # 奔跑路線從巷子到天橋
  # 2026-03-10 Bridge～Outro（Claude 代決：使用者授權自行完成，以下皆可改）
  letter_glow_meaning: warm_light      # Claude 代決：暖光表示信裡的話有溫度，與霓虹的冷色做出差異
  late_plot_review: later              # 重審關卡：做這些段落的關鍵幀之前（參考圖之後、試作之前）
```

### 使用者決定

- 註解寫使用者的選擇與原因（如果有說）。
- 使用者的意見若在別的檔案（例如審查時留的 `recommend.md`），在註解指到那個檔案。

### 「Claude 代決」

使用者授權 Claude 自行完成時（見 SKILL.md 的授權模式），劇情與設定題由 Claude 決定，必須：

1. 註解寫「Claude 代決」。
2. 寫一句理由（為什麼選這個、跟什麼做出差異）。
3. 在段落標題註明授權範圍，例如 `# 2026-03-10 Bridge～Outro（Claude 代決：使用者授權「自行完成所有任務直到 P3 結束」，以下皆可改）`。
4. 鏡頭與實體維持 `status: proposed`，不改 `confirmed`。
5. 延後的審查另開一列，寫明**重審的關卡**：

| 要記的事 | 範例 |
| --- | --- |
| 哪些項目延後 | `late_plot_review: later` |
| 重審關卡 | 「做這些段落的關鍵幀之前再審」「G1 animatic 時一起看」 |
| 影響範圍 | 哪些 shot id、哪些實體 |

重審時，把使用者的答案寫成新的日期段落；被改掉的 Claude 代決不要刪，加註解「改為 …（日期）」。

### 精度題的決定

critic 的精度題（尺寸、幀數、位置、時間、後製與模型分工）由 Claude 代決，理由寫在 review 檔的 `resolution`，不一定要進 decisions。
只有會影響後面段落的（例如「霓虹從巷子遠端往近端依序熄滅」）才升級成 decisions 的一列，並同步 glossary。

## review 檔

檔名 `plan/review/<段落>_r<輪>.yaml`，例如 `intro_r1.yaml`。一個檔案一輪、一個範圍。
第一輪由 plan-critic 產生；處理過程中由 Claude 填 `status`、`resolution`、`decided_by`。

### 檔頭

```yaml
# Intro（s001–s003）第 1 輪歧義審稿（plan-critic，Claude Sonnet，2026-03-03）
# status：open＝等回答；resolved＝已處理（resolution 寫怎麼處理）
round: intro_r1
issues:
```

### 每一題

```yaml
  - id: Q01
    where: shots.s001.beat_events[0].event     # 檔案.項目.欄位
    category: 2                                # plan-critic 檢查清單編號
    quote: 亮度略微提高                         # 原文逐字
    problem: 「略微」沒有數字，也沒有說幾幀內完成、幾幀回落，執行的人必須自己決定
    question: 粉紅霓虹色塊的 glow_pulse，亮度抬升到幾倍？抬升與回落各用幾幀？
    options: ["亮度 1 幀內抬升到約 1.5 倍，再用 3 幀回落，共 4 幀", "亮度 2 幀內抬升到約 2 倍，再用 4 幀回落"]
    severity: low
    status: resolved
    decided_by: claude
    resolution: "a：1 幀抬升到約 1.5 倍，3 幀回落。精度題，Claude 代決；理由：只是一個鼓點的提示，抬升太高會蓋過後面的亮度層次。"
```

完整的審稿檔見 `examples/neon-courier/plan/review/intro_r1.yaml`（含一題 `open`、一題使用者回答的 `resolved`）。

### 狀態

| 欄位 | 值 | 意思 |
| --- | --- | --- |
| `status` | `open` | 等回答；lint 列為 OPEN |
| `status` | `resolved` | 已處理；必須有 `resolution` |
| `decided_by` | `user` | 使用者回答（劇情與設定題） |
| `decided_by` | `claude` | Claude 代決（精度題，或使用者授權的劇情題） |
| `resolution` | 字串 | 選了哪個 option（`a`／`b`…）、改了哪些欄位、一句理由 |

- `decided_by` 是選填，也是本外掛新增的欄位；舊檔把「使用者授權 Claude 決定（日期）」直接寫在 `resolution` 開頭，兩種都可以，新檔建議用欄位。
- 只改文字、不改意思的題，`resolution` 寫改了哪裡就好（例如「構圖不變，改標 LS」）。
- 被駁回的題也要 `resolved`，`resolution` 寫駁回理由（例如「檔案 glossary.alley.look 已回答」）。
- Claude 自己查稿發現的題，可以接在後面編號，`question` 或 `resolution` 註明「Claude 自查」。

### 逐條處理的分流

| 題目類型 | 誰決定 | 記在哪 |
| --- | --- | --- |
| 劇情、設定、角色、結局、轉場類型 | 使用者（`AskUserQuestion`） | review 檔 `resolution`＋`decided_by: user`；影響後面段落的升級到 decisions |
| 尺寸、幀數、位置、時間、後製與模型分工 | Claude | review 檔 `resolution`＋`decided_by: claude`；理由必填 |
| 授權模式為「自行完成」時的劇情題 | Claude（代決） | review 檔與 decisions 都標「Claude 代決」；延後重審 |

處理完給使用者看**決策表**（題號、題目、決定、理由），不要丟問題清單。
使用者可以改任何一條；改了就更新 `resolution` 並重跑 lint。

### 與 lint 的關係

- `lint_plan.py` 會把 `status: open` 的題列為 OPEN（不影響結束碼）。
- 一段落結束時，review 檔不該有 `open`。要延後的題保持 `open`，並在 decisions 寫明重審關卡（例如 `late_plot_review: later`）。
