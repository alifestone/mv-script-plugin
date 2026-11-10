#!/usr/bin/env python3
"""檢查 MV 劇本目錄的結構化劇本（project、glossary、story、shots）；有 FAIL 時結束碼為 1。

python3 lint_plan.py --plan DIR [--timeline FILE] [--words FILE] [--schema DIR]
                     [--profile legacy|full] [--quiet]

  --plan      劇本目錄（內含 project.yaml、glossary.yaml、story.yaml、shots.yaml，可有 review/*.yaml）
  --timeline  timeline.json；預設讀 project.yaml 的 timeline 欄，相對路徑以「plan 目錄的上一層」解析
  --words     中文詞表（YAML）；預設 words/zh-TW.yaml
  --schema    JSON Schema 目錄；預設 schema/
  --profile   legacy＝只跑基本規則（G、R、T、S、W、N、Y）；full＝加跑 schema 與新規則（預設）
  --quiet     不列 OPEN 項目

檢查項目：
  G 名詞表   實體必填欄位、外觀是否定義
  R 引用     @id 是否存在、禁用別名與禁用母題、該用 @id 卻寫了名稱
  T 時間     span 是否落在拍點、鏡頭是否首尾相接、長度上限、beat_events 是否在鏡頭內
  S 鏡頭     必填欄位、詞彙值、主體位置／大小／面向、末幀、轉場參數、route 限制
  W 寫法     首幀寫了動作、模糊詞、「閃三次」這類沒拆成 beat_events 的序列
  N 敘事     段落是否齊全、敘事層混入鏡頭用語
  Y 語法     YAML 值裡的「 #」被當成註解吃掉
以下只在 --profile full：
  X1 結構    不符 schema/*.schema.json（必填欄位、型別、列舉）。FAIL
  V1 景別    ECU／CU 鏡頭的 first_frame 沒寫聚焦部位（詞表 focus_parts）。WARN（ViMax）
  V2 比喻    story 與 shots 文字出現比喻詞（詞表 metaphor_words，排除 metaphor_exclude 的複合詞）。WARN（ViMax「不准比喻」）
  F1 末幀    主體 state 含「→」或 motion.subject 寫了外觀變化（詞表 appearance_change，先排除 appearance_exclude），
             卻沒有 last_frame。WARN（F＝feasibility：影片模型做不做得到）
             同一子句同時含「閉」和「睜」視為眨眼，不報；variation 為 medium／large 時舊規則 S4 已經 FAIL，不重複報
  F2 朝向    motion.subject 的某個子句寫了轉向（turn_words）或水平行進（travel_words），子句裡動詞之前最近的 @id
             是動作主體；該主體的 facing 若是單一字串（不是依階段的 dict，如 {entering: ..., settled: ...}）。WARN
             上升、下降、落下這類垂直移動不算；子句裡沒有 @id 就不報；@id 與動詞之間有 part_words（視線、光帶…）
             表示轉的是部位而不是主體，也不報
  F3 靜臉    route A、景別 ECU／CU／MCU／MS（臉清楚可見）、character 主體沒有動作（motion.subject 沒寫它，
             或寫了詞表 still_words）時，first_frame 要同時含 face_state 的每一類（表情、嘴、眼）至少一個詞。INFO（只提醒：代名詞歸屬不可靠，
             實測誤報多；最終由 critic 12.3 判斷）
             「她他它牠」開頭（或沒有 @id 只有代名詞）的子句歸屬到前一個出現的 @id；整段都沒有 @id 時歸屬到本鏡
             唯一的 character（有兩個以上 character 就無法歸屬）。
             facing 為 away 的主體、glossary 實體寫了 no_face: true 的主體不檢查
  F4 拍點    同一鏡相鄰兩筆 beat_events 相隔不到 1 拍，且後一筆含 turn_words、travel_words 或 vertical_words（動詞後緊接「中」如「上升中」是狀態描述，不算）。WARN
  （F1–F4 是 WARN 層級的新代碼；OPEN 層級的 P1 仍是「status: proposed」，兩者不同。）
最後列出所有 status: proposed 的項目與 questions。
"""
import argparse, re, sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import schema_check  # noqa: E402

REF_RE = re.compile(r"@([a-z_][a-z0-9_]*)")

# ── 流程定義（結構常數，不是某支影片的內容）──────────────────────────
# 實體種類、影片路線（A＝一般 I2V、B＝指定動作（骨架／姿勢控制）、C＝靜態圖＋視差）、
# 動作由誰完成、需要末幀的景別、各種轉場必須帶的參數；改這些等於改流程本身。
KINDS = {"character", "place", "object", "vfx", "state"}
ROUTES = {"A", "B", "C"}
REALIZE = {"model", "post", "model+post", "none"}
CLOSE = {"ECU", "CU"}
FACE_SIZES = {"ECU", "CU", "MCU", "MS"}   # 臉清楚可見的景別（F3 只檢查這些）
TRANSITION_PARAMS = {"flash_white": [("frames",)], "whiteout": [("in_beats",), ("out_beats",)],
                     "fade_from_black": [("beats", "frames")], "fade_to_black": [("beats", "frames")],
                     "dissolve": [("beats", "frames")]}

DEFAULT_WORDS = HERE / "words" / "zh-TW.yaml"
OLD_WORD_KEYS = ("motion_words", "vague_words", "seq_re", "story_camera_words")
NEW_WORD_KEYS = ("focus_parts", "metaphor_words", "metaphor_exclude", "appearance_change", "appearance_exclude",
                 "turn_words", "travel_words", "vertical_words", "part_words", "face_state", "still_words")


class Words:
    """中文詞表；缺的鍵對應的規則略過（空清單、沒有 seq_re）。"""

    def __init__(self, data):
        self.data = data
        self.motion = data.get("motion_words") or []
        self.vague = data.get("vague_words") or []
        self.story_camera = data.get("story_camera_words") or []
        self.seq_re = re.compile(data["seq_re"]) if data.get("seq_re") else None

    def get(self, key):
        return self.data.get(key) or ([] if key != "face_state" else {})

    def missing(self, keys):
        return [k for k in keys if not self.data.get(k)]


def load_words(path):
    return Words(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})


def resolve_timeline(plan, project, override=None):
    """timeline 路徑：--timeline 優先；否則 project.yaml 的 timeline 欄，相對路徑以 plan 的上一層解析。"""
    if override:
        return Path(override)
    if not project.get("timeline"):
        raise SystemExit("找不到 timeline：project.yaml 沒有 timeline 欄，請用 --timeline 指定")
    return plan.resolve().parent / project["timeline"]


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, code, where, msg):
        self.rows.append((level, code, where, msg))

    def fail(self, *a): self.add("FAIL", *a)
    def warn(self, *a): self.add("WARN", *a)


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def texts(node, path=""):
    """逐一產生 (路徑, 字串)；跳過 questions（問題本身可以提到任何詞）。"""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k != "questions":
                yield from texts(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from texts(v, f"{path}[{i}]")


class Clock:
    """把 [小節, 拍] 換成秒；拍可為小數，在相鄰兩拍之間內插。"""

    def __init__(self, tl):
        self.duration = tl["meta"]["duration_sec"]
        self.bar_sec = tl["meta"]["bar_sec"]
        self.beats = sorted(tl["beats"], key=lambda b: b["t"])
        self.index = {(b["bar"], b["beat_in_bar"]): i for i, b in enumerate(self.beats)}
        self.bars = {b["bar"]: b for b in tl["bars"]}
        self.sections = {s["label"]: s for s in tl["sections"]}
        gaps = sorted(b2["t"] - b1["t"] for b1, b2 in zip(self.beats, self.beats[1:]))
        self.beat_sec = gaps[len(gaps) // 2] if gaps else self.bar_sec  # 一拍的秒數（取相鄰拍間隔的中位數）

    def t(self, pos):
        if pos == "end":
            return self.duration
        if not (isinstance(pos, list) and len(pos) == 2):
            raise ValueError(f"位置格式應為 [小節, 拍] 或 end：{pos!r}")
        bar, beat = pos
        if [bar, beat] == [0, 0]:
            return 0.0
        whole = int(beat)
        if (bar, whole) not in self.index:
            raise ValueError(f"[{bar},{beat}] 不是 timeline 裡的拍點")
        i = self.index[(bar, whole)]
        frac = beat - whole
        if frac == 0:
            return self.beats[i]["t"]
        nxt = self.beats[i + 1]["t"] if i + 1 < len(self.beats) else self.duration
        return self.beats[i]["t"] + frac * (nxt - self.beats[i]["t"])


def check_glossary(g, rep):
    vocab, ents = g.get("vocab", {}), g.get("entities", {})
    for eid, e in ents.items():
        w = f"glossary.{eid}"
        for f in ("kind", "name", "status", "definition"):
            if not e.get(f):
                rep.fail("G1", w, f"缺少 {f}")
        if e.get("kind") not in KINDS:
            rep.fail("G1", w, f"kind 應為 {sorted(KINDS)}")
        if e.get("kind") != "character" and not e.get("look"):
            rep.warn("G2", w, "外觀（look）尚未定義；寫到用它的鏡頭前要補上")
        if e.get("kind") == "character" and not (e.get("look") or e.get("refs")):
            rep.warn("G2", w, "角色沒有 look 也沒有參考圖 refs")
    return vocab, ents


def check_refs(docs, ents, banned, rep):
    names = {eid: e.get("name", "") for eid, e in ents.items()}
    aliases = {a: eid for eid, e in ents.items() for a in e.get("aliases_forbidden", []) or []}
    for doc_name, doc in docs:
        for path, s in texts(doc):
            where = f"{doc_name}:{path}"
            for rid in REF_RE.findall(s):
                if rid not in ents:
                    rep.fail("R1", where, f"@{rid} 不在名詞表")
            for a, eid in aliases.items():
                if ".aliases_forbidden[" in path:
                    break   # 禁用別名清單本身不算「使用」別名
                if a in s:
                    rep.fail("R2", where, f"用了禁用別名「{a}」，應寫 @{eid}")
            for b in banned:
                if b in s:
                    rep.fail("R2", where, f"出現已禁用的母題「{b}」")
            if doc_name == "glossary":
                continue
            plain = REF_RE.sub("", s)
            for eid, name in names.items():
                core = re.sub(r"（.*?）", "", name)
                if len(core) >= 2 and core in plain:
                    rep.warn("R3", where, f"寫了名稱「{core}」，應改成 @{eid}")


def check_writing(doc_name, doc, rep, W):
    for path, s in texts(doc):
        where = f"{doc_name}:{path}"
        hits = [w for w in W.vague if w in s]
        if hits:
            rep.warn("W2", where, f"模糊詞：{'、'.join(hits)}")
        if W.seq_re and W.seq_re.search(s) and "beat_events" not in path:
            rep.warn("W3", where, f"「{W.seq_re.search(s).group(0)}」這類序列要拆成 beat_events，一拍一筆")


def check_raw_comments(plan, rep):
    """YAML 的「空格＋#」會把後面當成註解吃掉（例如色碼 #29d3f5）；值裡有 # 就要加引號。"""
    pat = re.compile(r"^\s*(?:- )?[a-z_]+: ([^\"'\[{>|\s#][^#]*?)\s#\S")
    for name in ("glossary", "story", "shots"):
        for i, line in enumerate((plan / f"{name}.yaml").read_text(encoding="utf-8").splitlines(), 1):
            if pat.match(line):
                rep.fail("Y1", f"{name}.yaml:{i}", "值裡的「 #」之後會被 YAML 當成註解刪掉，請把整個值加上引號")


def check_story(story, clock, rep, W):
    beats = story.get("beats", [])
    seen = {b.get("section") for b in beats}
    for label, sec in clock.sections.items():
        if label not in seen:
            rep.fail("N1", "story", f"段落 {label}（bar {sec['bar_start']}–{sec['bar_end']}）沒有敘事")
    for b in beats:
        w = f"story.{b.get('id')}"
        for f in ("id", "section", "bars", "story", "emotion", "lyric_link", "status"):
            if not b.get(f):
                rep.fail("N2", w, f"缺少 {f}")
        sec = clock.sections.get(b.get("section"))
        if sec and b.get("bars") != [sec["bar_start"], sec["bar_end"]]:
            rep.fail("N2", w, f"bars 應為 [{sec['bar_start']}, {sec['bar_end']}]（timeline）")
        hits = [x for x in W.story_camera if x in (b.get("story") or "")]
        if hits:
            rep.warn("N3", w, f"敘事層混入鏡頭用語：{'、'.join(hits)}（畫面細節寫在 shots）")
    return {b.get("id") for b in beats}


def bars_spanned(span):
    """鏡頭碰到幾個小節（弱起的 bar 0 也算一個小節）；to 落在下一小節第 1 拍時不算進下一小節。"""
    a, b = span["from"], span["to"]
    if b == "end":
        return 1
    return (b[0] if b[1] == 1 else b[0] + 1) - a[0]


def need(d, keys, where, rep, code="S1"):
    for k in keys:
        if d.get(k) in (None, "", []):
            rep.fail(code, where, f"缺少 {k}")


def check_shots(shots, vocab, ents, story_ids, clock, tl, params, rep, W):
    lyric_ids = {l["id"] for l in tl["lyrics"]}
    prev = None
    for sh in shots:
        sid = sh.get("id", "?")
        w = f"shots.{sid}"
        need(sh, ["id", "section", "story_beat", "span", "place", "shot_size", "angle", "route", "variation",
                  "subjects", "first_frame", "motion", "transition_in", "status"], w, rep)
        # 詞彙值
        for key, voc in (("shot_size", "shot_size"), ("angle", "angle")):
            if sh.get(key) and sh[key] not in vocab.get(voc, {}):
                rep.fail("S2", w, f"{key}={sh[key]} 不在 vocab.{voc}")
        if sh.get("route") not in ROUTES:
            rep.fail("S2", w, f"route 應為 {sorted(ROUTES)}")
        if sh.get("variation") not in vocab.get("variation", {}):
            rep.fail("S2", w, f"variation={sh.get('variation')} 不在 vocab.variation")
        if sh.get("story_beat") and sh["story_beat"] not in story_ids:
            rep.fail("S2", w, f"story_beat={sh['story_beat']} 不在 story.yaml")
        for lid in sh.get("lyrics") or []:
            if lid not in lyric_ids:
                rep.fail("S2", w, f"歌詞 id {lid} 不存在")
        # 主體
        for i, sub in enumerate(sh.get("subjects") or []):
            sw = f"{w}.subjects[{i}]"
            need(sub, ["ref", "placement", "size"], sw, rep, "S3")
            rid = (REF_RE.findall(sub.get("ref", "")) or [None])[0]
            pl = sub.get("placement") or {}
            for axis, voc in (("x", "screen_x"), ("y", "screen_y"), ("depth", "depth")):
                if pl.get(axis) not in vocab.get(voc, []):
                    rep.fail("S3", sw, f"placement.{axis}={pl.get(axis)} 不在 vocab.{voc}")
            if rid in ents and ents[rid].get("kind") == "character":
                need(sub, ["facing", "state"], sw, rep, "S3")
                if isinstance(sub.get("facing"), dict):
                    # 依階段的 facing（{entering: ..., settled: ...}）：每個階段的值都要在 vocab.facing
                    for stage, fv in sub["facing"].items():
                        if fv not in vocab.get("facing", []):
                            rep.fail("S3", sw, f"facing.{stage}={fv} 不在 vocab.facing")
                elif sub.get("facing") and sub["facing"] not in vocab.get("facing", []):
                    rep.fail("S3", sw, f"facing={sub['facing']} 不在 vocab.facing")
        # 畫面裡寫到的實體，都要列在 subjects 或 place（才有位置與大小）
        listed = {(REF_RE.findall(x.get("ref", "")) or [None])[0] for x in sh.get("subjects") or []}
        listed |= set(REF_RE.findall(sh.get("place") or ""))
        body = {k: sh.get(k) for k in ("first_frame", "last_frame", "motion", "beat_events")}
        shown = {rid for _, t in texts(body) for rid in REF_RE.findall(t)}
        for rid in sorted(shown - listed):
            if ents.get(rid, {}).get("kind") not in ("place", "state"):
                rep.warn("S7", w, f"畫面裡寫到 @{rid}，但 subjects 沒有列出它的位置與大小")
        # 運動
        mo = sh.get("motion") or {}
        cam, subj = mo.get("camera") or {}, mo.get("subject") or {}
        if cam.get("move") not in vocab.get("camera_move", {}):
            rep.fail("S4", w, f"motion.camera.move={cam.get('move')} 不在 vocab.camera_move")
        if cam.get("speed") not in vocab.get("camera_speed", {}):
            rep.fail("S4", w, f"motion.camera.speed={cam.get('speed')} 不在 vocab.camera_speed")
        for part, d in (("camera", cam), ("subject", subj)):
            if d.get("realize") not in REALIZE:
                rep.fail("S4", w, f"motion.{part}.realize 應為 {sorted(REALIZE)}")
        if sh.get("variation") in ("medium", "large") and not sh.get("last_frame"):
            rep.fail("S4", w, f"variation={sh.get('variation')} 必須寫 last_frame")
        # 首幀不寫動作
        hits = [x for x in W.motion if x in (sh.get("first_frame") or "")]
        if hits:
            rep.warn("W1", w, f"first_frame 應是靜止畫面，出現動作詞：{'、'.join(hits)}")
        # 轉場
        tr = sh.get("transition_in") or {}
        ttype = tr.get("type")
        if ttype not in vocab.get("transition", {}):
            rep.fail("S5", w, f"transition_in.type={ttype} 不在 vocab.transition")
        for alts in TRANSITION_PARAMS.get(ttype, []):
            if not any(tr.get(a) for a in alts):
                rep.fail("S5", w, f"{ttype} 需要參數 {' 或 '.join(alts)}")
        if ttype == "match_cut" and not tr.get("note"):
            rep.fail("S5", w, "match_cut 要在 note 寫出前後對齊的是什麼")
        # 時間
        span = sh.get("span") or {}
        try:
            t0, t1 = clock.t(span.get("from")), clock.t(span.get("to"))
        except (ValueError, TypeError) as e:
            rep.fail("T1", w, str(e))
            prev = sh
            continue
        dur = t1 - t0
        if dur <= 0:
            rep.fail("T1", w, "span.to 必須晚於 span.from")
        nbars = bars_spanned(span)
        if nbars > params.get("max_shot_bars", 2):
            rep.fail("T2", w, f"跨 {nbars} 小節（{dur:.2f} s），超過 {params.get('max_shot_bars', 2)} 小節上限")
        if prev is None and span.get("from") != [0, 0]:
            rep.fail("T3", w, "第一鏡應從 [0, 0] 開始")
        if prev is not None and (prev.get("span") or {}).get("to") != span.get("from"):
            rep.fail("T3", w, f"與上一鏡 {prev.get('id')} 沒有首尾相接（{(prev.get('span') or {}).get('to')} ≠ {span.get('from')}）")
        sec = clock.sections.get(sh.get("section"))
        bar0 = span["from"][0] if isinstance(span.get("from"), list) else None
        if sec and bar0 is not None and not (sec["bar_start"] <= bar0 <= sec["bar_end"]):
            rep.fail("T4", w, f"起點 bar {bar0} 不在段落 {sh['section']}（bar {sec['bar_start']}–{sec['bar_end']}）內")
        for j, ev in enumerate(sh.get("beat_events") or []):
            try:
                te = clock.t(ev.get("at"))
            except (ValueError, TypeError) as e:
                rep.fail("T5", f"{w}.beat_events[{j}]", str(e))
                continue
            if not (t0 <= te < t1):
                rep.fail("T5", f"{w}.beat_events[{j}]", f"{ev.get('at')} 不在本鏡時間內")
            if not ev.get("event"):
                rep.fail("T5", f"{w}.beat_events[{j}]", "缺少 event")
        # route 限制（見計畫書「影片路線與模型」）
        if sh.get("route") == "C":
            if nbars > 1:
                rep.fail("S6", w, "route C 鏡頭不得超過 1 小節")
            if sh.get("shot_size") in CLOSE:
                rep.fail("S6", w, "route C（視差）不用於特寫")
            if subj.get("realize") in ("model", "model+post"):
                rep.fail("S6", w, "route C 是靜態圖＋視差，主體動作只能由後製做（realize: post）")
        prev = sh
    if prev is not None:
        try:
            end = clock.t((prev.get("span") or {}).get("to"))
            rep.add("INFO", "T6", "shots", f"鏡頭覆蓋到 {end:.2f} s／全曲 {clock.duration:.2f} s")
        except (ValueError, TypeError):
            pass


def flat(x):
    """把字串或（依階段的）dict／list 攤平成一段文字。"""
    if x is None:
        return ""
    if isinstance(x, dict):
        return " ".join(flat(v) for v in x.values())
    if isinstance(x, list):
        return " ".join(flat(v) for v in x)
    return str(x)


def hits_in(words, text):
    return [w for w in words if w in text]


def sentences(text):
    return [t for t in re.split(r"[。；;\n]", text) if t.strip()]


def clauses(text):
    """子句：以「，。；、」與換行切開。"""
    return [t for t in re.split(r"[，。；;、\n]", text) if t.strip()]


def active_hits(words, text):
    """hits_in，但動詞後面緊接「中」（上升中）是狀態描述，不算動作。"""
    return [w for w in words if any(text[m.end():m.end() + 1] != "中" for m in re.finditer(re.escape(w), text))]


def mover_hits(text, words, parts=()):
    """每個含 words 的子句，取動詞之前最近的 @id 當動作主體；子句裡動詞前沒有 @id 就略過。回傳 {id: [詞]}。
    @id 到動詞之間若有 parts 的詞（視線、光帶…），表示轉的是身體部位而不是主體，也略過。"""
    movers = {}
    for c in clauses(text):
        verbs = [(c.index(w), w) for w in words if w in c]
        if not verbs:
            continue
        pos, _ = min(verbs)
        ids = [m for m in REF_RE.finditer(c) if m.start() < pos]
        if not ids or hits_in(parts, c[ids[-1].end():pos]):
            continue
        lst = movers.setdefault(ids[-1].group(1), [])
        lst += [w for _, w in sorted(verbs) if w not in lst]
    return movers


PRONOUNS = ("她", "他", "它", "牠")


def own_text(text, rid, chars):
    """motion.subject 裡屬於 rid 的文字：含 @rid 的句子，加上歸屬到它的代名詞子句。
    代名詞子句＝以「她他它牠」開頭，或沒有 @id 但含代名詞；歸屬到前一個出現 @id 的子句裡的第一個 @id；
    整段都沒有 @id 時歸屬到本鏡唯一的 character（chars 只有一個時）。"""
    own = [t for t in sentences(text) if f"@{rid}" in t]
    last = None
    for c in clauses(text):
        ids = REF_RE.findall(c)
        pron = c.lstrip().startswith(PRONOUNS) or (not ids and any(p in c for p in PRONOUNS))
        if pron:
            who = last or (chars[0] if len(chars) == 1 and not REF_RE.search(text) else None)
            if who == rid:
                own.append(c)
        if ids and not c.lstrip().startswith(PRONOUNS):
            last = ids[0]
    return own


def sub_ref(sub):
    return (REF_RE.findall(sub.get("ref") or "") or [None])[0]


def check_metaphor(docs, rep, W):
    """V2：story 與 shots 文字不准比喻。先移除 metaphor_exclude 的複合詞（影像、畫像…）再比對。"""
    if W.missing(["metaphor_words"]):
        return
    for doc_name, doc in docs:
        if doc_name not in ("story", "shots"):
            continue
        for path, s in texts(doc):
            plain = s
            for ex in sorted(W.get("metaphor_exclude"), key=len, reverse=True):
                plain = plain.replace(ex, "")
            hits = hits_in(W.get("metaphor_words"), plain)
            if hits:
                rep.warn("V2", f"{doc_name}:{path}", f"比喻詞：{'、'.join(hits)}（改成直接描述畫面）")


def check_shots_extra(shots, ents, clock, rep, W):
    """V1、F1–F4：full profile 新增的鏡頭規則；詞表缺哪一項就略過那條規則。"""
    turn, travel, vert = W.get("turn_words"), W.get("travel_words"), W.get("vertical_words")
    on = {"V1": not W.missing(["focus_parts"]), "F1": not W.missing(["appearance_change"]),
          "F2": bool(turn or travel), "F3": not W.missing(["face_state"]), "F4": bool(turn or travel or vert)}
    for sh in shots:
        w = f"shots.{sh.get('id', '?')}"
        subjects = [x for x in (sh.get("subjects") or []) if isinstance(x, dict)]
        ff = sh.get("first_frame") or ""
        mo = sh.get("motion") or {}
        subj_text = (mo.get("subject") or {}).get("text") or ""
        # V1：特寫要寫聚焦部位
        if on["V1"] and sh.get("shot_size") in CLOSE and not hits_in(W.get("focus_parts"), ff):
            rep.warn("V1", w, f"景別 {sh.get('shot_size')} 的 first_frame 沒有寫聚焦的部位（例如：{'、'.join(W.get('focus_parts')[:6])}…）")
        # F1：會改變外觀的鏡頭要寫 last_frame
        if on["F1"] and not sh.get("last_frame") and sh.get("variation") not in ("medium", "large"):
            arrows = [sub_ref(x) or "?" for x in subjects if "→" in flat(x.get("state"))]
            words = []
            for c in clauses(subj_text):
                if "閉" in c and "睜" in c:
                    continue   # 閉眼再睜開＝眨眼，首尾幀相同
                for ex in W.get("appearance_exclude"):
                    c = c.replace(ex, "")
                words += [x for x in hits_in(W.get("appearance_change"), c) if x not in words]
            if arrows or words:
                why = []
                if arrows:
                    why.append(f"@{'、@'.join(arrows)} 的 state 有「→」")
                if words:
                    why.append(f"motion.subject 寫了{'、'.join(words)}")
                rep.warn("F1", w, f"{'；'.join(why)}，但沒有 last_frame")
        # F2：轉向／水平行進的主體，facing 要依階段寫 dict
        if on["F2"]:
            movers = mover_hits(subj_text, turn + travel, W.get("part_words"))
            for x in subjects:
                rid = sub_ref(x)
                if rid in movers and isinstance(x.get("facing"), str):
                    rep.warn("F2", w, f"motion.subject 對 @{rid} 寫了{'、'.join(movers[rid])}，但 facing 是單一值「{x['facing']}」；"
                                      "請改成依階段的 dict（例如 {entering: ..., settled: ...}）")
        # F3：route A 的靜止角色，first_frame 要寫表情、嘴、眼
        if on["F3"] and sh.get("route") == "A" and sh.get("shot_size") in FACE_SIZES:
            for x in subjects:
                rid = sub_ref(x)
                if ents.get(rid, {}).get("kind") != "character" or ents[rid].get("no_face"):
                    continue   # glossary 實體可寫 no_face: true（例如無臉的機器人）免檢查
                fv = x.get("facing")
                if fv == "away" or (isinstance(fv, dict) and fv and set(fv.values()) == {"away"}):
                    continue   # 背對鏡頭，看不到臉
                chars = [sub_ref(y) for y in subjects if ents.get(sub_ref(y), {}).get("kind") == "character"]
                own = own_text(subj_text, rid, chars)
                still = hits_in(W.get("still_words"), " ".join(own))
                if own and not (still and all(hits_in(W.get("still_words"), t) for t in own)):
                    continue   # 有寫它的動作
                lack = [cat for cat, ws in W.get("face_state").items() if not hits_in(ws, ff)]
                if lack:
                    rep.add("INFO", "F3", w, f"@{rid} 在本鏡沒有動作，first_frame 要寫臉部狀態，缺：{'、'.join(lack)}")
        # F4：相鄰拍點間距不足 1 拍，後一筆又是位移／轉向
        if on["F4"]:
            evs = [e for e in (sh.get("beat_events") or []) if isinstance(e, dict)]
            for j in range(1, len(evs)):
                try:
                    ta, tb = clock.t(evs[j - 1].get("at")), clock.t(evs[j].get("at"))
                except (ValueError, TypeError):
                    continue
                mv = active_hits(turn + travel + vert, flat(evs[j].get("event")))
                if 0 <= tb - ta < clock.beat_sec - 1e-6 and mv:
                    rep.warn("F4", f"{w}.beat_events[{j}]",
                             f"與上一筆只差 {(tb - ta) / clock.beat_sec:.2f} 拍（不到 1 拍），卻寫了{'、'.join(mv)}；動作太趕，拉開或拆鏡")


def pretty_path(doc_name, doc, path):
    """schema 錯誤的位置：把 shots[3]、beats[1]、entities.hero 換成 id，好找。"""
    parts, node = [], doc
    for i, key in enumerate(path):
        child = node.get(key) if isinstance(node, dict) else (node[key] if isinstance(node, list) and key < len(node) else None)
        if isinstance(key, int) and isinstance(child, dict) and child.get("id") and i <= 1:
            parts.append(str(child["id"]))
        elif i == 0 and key in ("shots", "beats", "entities"):
            pass   # 最上層的清單／表名省略，直接接 id
        elif isinstance(key, int):
            parts[-1:] = [f"{parts[-1]}[{key}]"] if parts else [f"[{key}]"]
        else:
            parts.append(str(key))
        node = child
    return ".".join([doc_name] + parts)


def check_schema(named_docs, schema_dir, rep):
    """X1：依 schema 目錄檢查四份 YAML 的結構；回傳是否有錯。"""
    bad = False
    for name, doc in named_docs:
        sch = schema_check.load_schema(schema_dir, name)
        if sch is None:
            print(f"（略過 {name} 的 schema 檢查：{schema_dir} 裡沒有 {name}.schema.json）", file=sys.stderr)
            continue
        for path, msg in schema_check.check(doc, sch):
            bad = True
            rep.fail("X1", pretty_path(name, doc, path), msg)
    return bad


def collect_reviews(plan, rep):
    for f in sorted((plan / "review").glob("*.yaml")):
        for it in (load(f).get("issues") or []):
            if it.get("status") == "open":
                rep.add("OPEN", "Q2", f"{f.stem}.{it.get('id')} {it.get('where')}", it.get("question"))


def collect_open(docs, rep):
    for doc_name, doc in docs:
        items = []
        if doc_name == "glossary":
            items = [(f"glossary.{k}", v) for k, v in (doc.get("entities") or {}).items()]
        elif doc_name == "story":
            items = [("story", doc)] + [(f"story.{b.get('id')}", b) for b in doc.get("beats", [])]
        elif doc_name == "shots":
            items = [(f"shots.{s.get('id')}", s) for s in doc.get("shots", [])]
        for where, d in items:
            if d.get("status") == "proposed":
                rep.add("OPEN", "P1", where, "status: proposed（待使用者確認）")
            for q in d.get("questions") or []:
                rep.add("OPEN", "Q1", where, q)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, help="劇本目錄")
    ap.add_argument("--timeline", help="timeline.json；預設讀 project.yaml 的 timeline 欄")
    ap.add_argument("--words", default=str(DEFAULT_WORDS), help="中文詞表 YAML")
    ap.add_argument("--schema", default=str(schema_check.DEFAULT_DIR), help="JSON Schema 目錄")
    ap.add_argument("--profile", choices=("legacy", "full"), default="full",
                    help="legacy＝只跑舊規則；full＝加跑 schema（X1）與新規則（V1、V2、F1–F4）")
    ap.add_argument("--quiet", action="store_true", help="不列 OPEN 項目")
    args = ap.parse_args()
    plan = Path(args.plan)
    full = args.profile == "full"

    project = load(plan / "project.yaml")
    glossary, story, shots = (load(plan / f"{n}.yaml") for n in ("glossary", "story", "shots"))
    tl = yaml.safe_load(resolve_timeline(plan, project, args.timeline).read_text(encoding="utf-8"))
    clock = Clock(tl)
    params = project.get("params", {})
    banned = (project.get("decisions") or {}).get("banned_motifs", [])
    W = load_words(args.words)
    absent = W.missing(OLD_WORD_KEYS + (NEW_WORD_KEYS if full else ()))
    if absent:
        print(f"（詞表 {args.words} 缺少：{'、'.join(absent)}；對應的規則略過）", file=sys.stderr)

    rep = Report()
    docs = [("glossary", glossary), ("story", story), ("shots", shots)]
    structure_bad = False
    if full:
        structure_bad = check_schema([("project", project)] + docs, args.schema, rep)
    try:
        check_raw_comments(plan, rep)
        vocab, ents = check_glossary(glossary, rep)
        check_refs(docs, ents, banned, rep)
        for name, doc in docs[1:]:
            check_writing(name, doc, rep, W)
        story_ids = check_story(story, clock, rep, W)
        check_shots(shots.get("shots", []), vocab, ents, story_ids, clock, tl, params, rep, W)
        if full:
            check_metaphor(docs, rep, W)
            check_shots_extra(shots.get("shots", []), ents, clock, rep, W)
    except (AttributeError, TypeError, KeyError) as e:
        if not structure_bad:
            raise
        rep.fail("X1", "lint", f"結構錯誤使語意檢查中斷（{type(e).__name__}: {e}）；先修好上面的 X1 再重跑")
    if not args.quiet:
        collect_open(docs, rep)
        collect_reviews(plan, rep)

    order = {"FAIL": 0, "WARN": 1, "INFO": 2, "OPEN": 3}
    for level, code, where, msg in sorted(rep.rows, key=lambda r: order[r[0]]):
        print(f"{level:4} {code} {where}: {msg}")
    n = {k: sum(r[0] == k for r in rep.rows) for k in order}
    print(f"\nFAIL {n['FAIL']}  WARN {n['WARN']}  OPEN {n['OPEN']}")
    sys.exit(1 if n["FAIL"] else 0)


if __name__ == "__main__":
    main()
