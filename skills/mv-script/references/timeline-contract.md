# timeline.json 合約（流程步驟 0）

本外掛不分析音樂。劇本流程開始前，使用者要先有一份符合下列合約的 `timeline.json`（例如 P1 音樂分析的產出）。
`lint_plan.py` 的 `Clock` 類別讀它；沒有它就不能算時間、不能開始寫鏡頭。

## lint 實際讀的欄位

| 路徑 | 型別 | 用途 |
| --- | --- | --- |
| `meta.duration_sec` | 數字 | 全曲秒數；`span` 寫 `end` 時換成這個值；最後一鏡的覆蓋檢查（T6） |
| `meta.bar_sec` | 數字 | 一小節秒數；beat_events 間距的備用值 |
| `beats[]` | 陣列 | 每個拍點一筆；lint 依 `t` 排序 |
| `beats[].t` | 數字（秒） | 拍點時間；小數拍在相鄰兩拍之間線性內插 |
| `beats[].bar` | 整數 | 小節編號；弱起的拍是 0 |
| `beats[].beat_in_bar` | 整數（1 起） | 小節內第幾拍；不規則小節（3 拍、5 拍）照實寫 |
| `bars[]` | 陣列 | 小節表 |
| `bars[].bar` | 整數 | 小節編號 |
| `sections[]` | 陣列 | 段落表；story 的 `section` 與鏡頭的 `section` 都對它 |
| `sections[].label` | 字串 | 段落名（intro、verse…）；story beat 與鏡頭用同一個字串 |
| `sections[].bar_start`、`bar_end` | 整數 | 段落起訖小節（含）；story 的 `bars` 必須等於 `[bar_start, bar_end]`（N2） |
| `lyrics[]` | 陣列 | 歌詞行 |
| `lyrics[].id` | 整數或字串 | 鏡頭的 `lyrics: [id]` 必須存在（S2） |

其他欄位（`frame`、`is_downbeat`、`energy`、`lyrics[].text`、`t_start`…）lint 不讀，但下游（P5 以後）會用，建議保留：

| 路徑 | 下游用途 |
| --- | --- |
| `meta.fps`、`meta.n_frames` | 切點換算 `frame = round(t × fps)` |
| `meta.bpm`、`beats_per_bar`、`beat_sec` | 速度與拍長 |
| `beats[].frame` | 絕對幀號 |
| `sections[].t_start`、`t_end`、`frame_start`、`frame_end` | 段落切點 |
| `lyrics[].text`、`t_start`、`t_end`、`bar_start`、`bar_end` | 歌詞對應 |

## 位置規則

- `[小節, 拍]` 必須是 `beats[]` 裡存在的 `(bar, beat_in_bar)`，否則 lint 報 T1。
- `[0, 0]` 是歌曲開頭，固定等於 0 秒，不需要 beats 裡有這一筆。
- 小數拍：`[2, 2.5]` 位於 `[2, 2]` 與 `[2, 3]` 之間；小節最後一拍的小數，內插到下一個拍點。
- 一拍的秒數 lint 取相鄰拍間隔的中位數，用來判斷 P4（相鄰拍點不到 1 拍）。

## 最小範例

[templates/timeline.example.json](../templates/timeline.example.json)（可直接給 lint 用，只有一個段落）：

```json
{
 "meta": {"duration_sec": 12.0, "bar_sec": 2.0, "fps": 24, "n_frames": 288, "bpm": 120, "beats_per_bar": 4, "beat_sec": 0.5},
 "beats": [
  {"i": 0, "t": 1.5, "frame": 36, "bar": 0, "beat_in_bar": 4, "is_downbeat": false},
  {"i": 1, "t": 2.0, "frame": 48, "bar": 1, "beat_in_bar": 1, "is_downbeat": true},
  {"i": 2, "t": 2.5, "frame": 60, "bar": 1, "beat_in_bar": 2, "is_downbeat": false}
 ],
 "bars": [{"bar": 1, "t_start": 2.0, "t_end": 4.0, "section": "intro", "lyric_ids": [1]}],
 "sections": [{"label": "intro", "bar_start": 0, "bar_end": 4, "t_start": 0.0, "t_end": 10.0}],
 "lyrics": [{"id": 1, "text": "範例歌詞第一行", "t_start": 2.0, "t_end": 5.5, "bar_start": 1, "bar_end": 2, "section": "intro"}]
}
```

上例是為了表格短而截斷的版本；完整檔案的 beats 要涵蓋所有被 `span`、`beat_events` 用到的拍點。

## 驗證 timeline 本身

開始寫鏡頭前先確認：

- 全部 `beats[].t` 單調遞增，相鄰間隔接近常數（弱起與不規則小節除外）。
- 每個 `sections[]` 的 `bar_start`、`bar_end` 在 `bars[]` 裡找得到；段落首尾相接。
- 歌詞 `bar_start`、`bar_end` 落在所屬段落內。
- 不規則小節已在 beats 裡照實寫（例如某小節只有 3 拍）。

## P1 的經驗

這些來自一支完整 MV 的 P1（音樂分析）經驗，做 timeline 時照辦：

- **拍點用 stem 做客觀驗證，不靠使用者聽。** 先把歌分軌（鼓、人聲），量鼓 onset 與拍點的偏差，再給使用者看數字。聽感容易被人聲與延遲誤導。
- **英文 hook 的人聲時間用 onset 偵測比 whisper 可靠。** 例如「3、2、1、GO」，在人聲 stem 上做 onset detection（如 librosa 的 `onset_detect`）量得的時間，比 whisper 的字詞時間穩。whisper 適合中文歌詞行的大致起訖。
- 人聲落點寫進 `beat_events.sync`，並標明量法（「人聲分軌加 onset」）。
- 不規則小節要在音樂分析階段修正（人工指定該小節的拍數），不要在劇本裡湊。
- 段落邊界與聽感的誤差要小於 1 拍；超過就改 `sections`，不要讓鏡頭去遷就。
