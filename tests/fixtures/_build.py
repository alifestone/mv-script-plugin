#!/usr/bin/env python3
"""產生 tests/fixtures/<規則>/{bad,ok}/ 的最小 plan＋timeline。

每個規則兩份：bad＝會觸發該規則、ok＝同一份劇本改到不觸發。改 fixture 請改這支再重跑，不要手改產物：
python3 tests/fixtures/_build.py
"""
import copy, json, shutil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

TIMELINE = {
    "meta": {"duration_sec": 5.0, "bar_sec": 2.0, "beat_sec": 0.5},
    "beats": [{"t": 0.5, "bar": 0, "beat_in_bar": 4}] + [
        {"t": 1.0 + 0.5 * i, "bar": 1 + i // 4, "beat_in_bar": 1 + i % 4} for i in range(8)],
    "bars": [{"bar": 1}, {"bar": 2}],
    "sections": [{"label": "intro", "bar_start": 0, "bar_end": 2}],
    "lyrics": [{"id": 1, "text": "測試"}],
}

PROJECT = {"schema_version": 1, "title": "Fixture MV", "timeline": "analysis/timeline.json",
           "params": {"max_shot_bars": 2}, "decisions": {"banned_motifs": []}}

GLOSSARY = {
    "vocab": {
        "shot_size": {"CU": "特寫", "MS": "中景", "LS": "遠景"},
        "angle": {"eye": "平視"},
        "camera_move": {"static": "不動"},
        "camera_speed": {"slow": "慢"},
        "variation": {"small": "小", "medium": "中", "large": "大"},
        "transition": {"cut": "直切"},
        "screen_x": ["center"], "screen_y": ["middle"], "depth": ["mg"],
        "facing": ["to_camera", "away"],
    },
    "entities": {
        "hero": {"kind": "character", "name": "艾拉", "status": "confirmed", "definition": "主角", "look": {"outfit": "白衣"}},
        "room": {"kind": "place", "name": "小房間", "status": "confirmed", "definition": "只有一面牆的房間", "look": {"wall": "灰牆"}},
    },
}

STORY = {"beats": [{"id": "intro", "section": "intro", "bars": [0, 2], "story": "@hero 站在 @room 裡等待。",
                    "emotion": "安靜", "lyric_link": "測試", "status": "confirmed"}]}

SHOT = {
    "id": "s001", "section": "intro", "story_beat": "intro", "span": {"from": [0, 0], "to": [2, 1]},
    "lyrics": [1], "place": "@room", "shot_size": "MS", "angle": "eye", "route": "A", "variation": "small",
    "subjects": [{"ref": "@hero", "placement": {"x": "center", "y": "middle", "depth": "mg"}, "size": "腰以上",
                  "facing": "to_camera", "state": "站著，表情平靜，嘴唇輕閉，雙眼看向鏡頭"}],
    "first_frame": "@hero 站在 @room 中央，表情平靜，嘴角放鬆，雙眼直視鏡頭。",
    "motion": {"camera": {"move": "static", "speed": "slow", "realize": "none"},
               "subject": {"text": "@hero 不動，只有呼吸起伏。", "realize": "none"}},
    "last_frame": None, "beat_events": [],
    "transition_in": {"type": "cut"}, "post": [], "overlay": None, "status": "confirmed",
}


def base():
    return {"project": copy.deepcopy(PROJECT), "glossary": copy.deepcopy(GLOSSARY),
            "story": copy.deepcopy(STORY), "shots": {"shots": [copy.deepcopy(SHOT)]}}


def shot(plan):
    return plan["shots"]["shots"][0]


def mut_X1(p, bad):
    if bad:
        shot(p)["status"] = "draft"          # 列舉：status 只能 proposed|confirmed


def mut_V1(p, bad):
    s = shot(p)
    s["shot_size"] = "CU"
    s["first_frame"] = ("@hero 站在 @room 中央，表情平靜，直視鏡頭。" if bad
                        else "@hero 的臉佔滿畫面，表情平靜，嘴角放鬆，雙眼直視鏡頭。")


def mut_V2(p, bad):
    p["story"]["beats"][0]["story"] = ("@hero 像一陣風衝進 @room。" if bad
                                       else "@hero 面對牆上的影像與畫像，停下腳步。")


def mut_F1(p, bad):
    s = shot(p)
    s["motion"]["subject"]["text"] = "@hero 轉身面向牆壁。"
    s["motion"]["subject"]["realize"] = "model"
    s["subjects"][0]["facing"] = {"entering": "to_camera", "settled": "away"}   # 避免同時觸發 F2
    if not bad:
        s["last_frame"] = "@hero 背對鏡頭站在 @room 中央，面向牆壁。"


def mut_F2(p, bad):
    s = shot(p)
    s["motion"]["subject"] = {"text": "@hero 走向 @room 深處。", "realize": "model"}
    s["subjects"][0]["facing"] = "to_camera" if bad else {"entering": "away", "settled": "to_camera"}


def mut_F3(p, bad):
    s = shot(p)
    s["motion"]["subject"] = {"text": "@room 的燈光保持穩定。", "realize": "none"}
    s["first_frame"] = ("@hero 站在 @room 中央。" if bad
                        else "@hero 站在 @room 中央，表情平靜，嘴角放鬆，雙眼直視鏡頭。")


def mut_F4(p, bad):
    s = shot(p)
    s["beat_events"] = [{"at": [1, 1], "event": "@room 的燈亮起"},
                        {"at": [1, 1.5] if bad else [1, 3], "event": "@hero 走向 @room 深處"}]


MUTATIONS = {k[4:]: v for k, v in globals().items() if k.startswith("mut_")}


def write(case, plan):
    root = HERE / case
    if root.exists():
        shutil.rmtree(root)
    (root / "plan").mkdir(parents=True)
    (root / "analysis").mkdir()
    (root / "analysis" / "timeline.json").write_text(json.dumps(TIMELINE, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for name, doc in plan.items():
        (root / "plan" / f"{name}.yaml").write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")


if __name__ == "__main__":
    shutil.rmtree(HERE / "P1", ignore_errors=True)    # 舊代碼 P1–P4 已改名 F1–F4
    for old in ("P1", "P2", "P3", "P4"):
        shutil.rmtree(HERE / old, ignore_errors=True)
    write("base/ok", base())
    for rule, mut in MUTATIONS.items():
        for bad in (True, False):
            p = base()
            mut(p, bad)
            write(f"{rule}/{'bad' if bad else 'ok'}", p)
    def extra(case, rule_mut, bad, edit):
        p = base()
        rule_mut(p, bad)
        edit(p)
        write(case, p)

    def set_text(p, text):
        shot(p)["motion"]["subject"]["text"] = text

    extra("F1/bad_arrow", mut_F1, True, lambda p: (set_text(p, "@hero 不動。"), shot(p)["subjects"][0].update(state="站著 → 蹲下")))
    extra("F1/ok_blink", mut_F1, True, lambda p: set_text(p, "@hero 輕輕吸一口氣、閉一下眼再睜開，然後眨眼一次。"))   # 眨眼不算外觀變化
    extra("F2/ok_vertical", mut_F2, True, lambda p: set_text(p, "@hero 隨平台上升到 @room 上方。"))                 # 垂直移動不算
    extra("F2/ok_noid", mut_F2, True, lambda p: set_text(p, "@hero 站著不動，遠處的雲滑入畫面。"))                    # 動詞前沒有 @id
    extra("F3/ok_far", mut_F3, True, lambda p: shot(p).update(shot_size="LS"))                                       # 遠景不檢查
    def add_bot(p):                 # 第二個角色（沒有臉），讓代名詞無法歸屬
        p["glossary"]["entities"]["bot"] = {"kind": "character", "name": "小機", "status": "confirmed",
                                            "definition": "無臉機器人", "look": {"shape": "球"}, "no_face": True}
        shot(p)["subjects"].append({"ref": "@bot", "placement": {"x": "center", "y": "middle", "depth": "mg"}, "size": "小", "facing": "away", "state": "懸浮"})
        shot(p)["first_frame"] += " @bot 懸在旁邊。"

    extra("F2/ok_part", mut_F2, True, lambda p: set_text(p, "@hero 的視線轉向 @room 深處。"))                         # 轉的是部位（視線）
    extra("F3/ok_pronoun", mut_F3, True, lambda p: set_text(p, "她輕輕抬起右手。"))                                    # 整段沒有 @id＋只有一個角色
    extra("F3/ok_pronoun_prev", mut_F3, True, lambda p: set_text(p, "@hero 站在原地，她輕輕抬起右手。"))                # 歸屬到前一個 @id
    extra("F3/bad_two_chars", mut_F3, True, lambda p: (add_bot(p), set_text(p, "她輕輕抬起右手。")))                   # 兩個角色：無法歸屬，仍報
    extra("F4/ok_state", mut_F4, True, lambda p: shot(p)["beat_events"][1].update(event="@hero 上升中"))              # 「上升中」是狀態
    extra("F4/bad_vertical", mut_F4, True, lambda p: shot(p)["beat_events"][1].update(event="@hero 上升到 @room 上方"))
    print("fixtures 已重新產生：", ", ".join(["base", *MUTATIONS]))
