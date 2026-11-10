#!/usr/bin/env python3
"""JSON Schema 結構檢查：有安裝 jsonschema 就用它；沒有就用內建的小型驗證器。

內建驗證器只支援 schema/ 裡用到的子集：
  type（含型別清單）、enum、const、required、properties、items、additionalProperties（布林或 schema）、
  $ref（只限同檔 #/$defs/...）、anyOf、oneOf、allOf、minItems、maxItems、minimum、minLength。
其他關鍵字會被忽略（不報錯）。要用更完整的 JSON Schema 功能，請安裝 jsonschema。
環境變數 MV_SCHEMA_BUILTIN=1 可強制用內建驗證器（測試用）。

check(doc, schema) 回傳 [(路徑 tuple, 訊息)]；空清單代表通過。
"""
import json
import os
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

SCHEMA_NAMES = ("project", "glossary", "story", "shots")
DEFAULT_DIR = Path(__file__).resolve().parent / "schema"


def backend():
    return "jsonschema" if jsonschema and not os.environ.get("MV_SCHEMA_BUILTIN") else "builtin"


def load_schema(directory, name):
    """讀 <directory>/<name>.schema.json；檔案不存在回傳 None。"""
    p = Path(directory) / f"{name}.schema.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}
_ZH = {"object": "物件", "array": "清單", "string": "字串", "boolean": "布林", "integer": "整數", "number": "數字", "null": "null"}


def _type_name(v):
    for t in ("null", "boolean", "integer", "number", "string", "array", "object"):
        if _TYPES[t](v):
            return _ZH[t]
    return type(v).__name__


def _resolve(ref, root):
    if not ref.startswith("#/"):
        raise ValueError(f"內建驗證器只支援同檔 $ref：{ref}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _validate(v, s, root, path, errs):
    if "$ref" in s:
        _validate(v, _resolve(s["$ref"], root), root, path, errs)
    if "type" in s:
        types = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(_TYPES[t](v) for t in types):
            errs.append((path, f"型別應為 {' 或 '.join(_ZH[t] for t in types)}，實際是 {_type_name(v)}"))
            return
    if "const" in s and v != s["const"]:
        errs.append((path, f"值應為 {s['const']!r}，實際是 {v!r}"))
    if "enum" in s and v not in s["enum"]:
        errs.append((path, f"值 {v!r} 不在允許的列舉 {s['enum']}"))
    if "minimum" in s and _TYPES["number"](v) and v < s["minimum"]:
        errs.append((path, f"值 {v} 小於下限 {s['minimum']}"))
    if "minLength" in s and isinstance(v, str) and len(v) < s["minLength"]:
        errs.append((path, f"字串長度小於 {s['minLength']}"))
    for key in ("anyOf", "oneOf"):
        if key in s:
            ok = []
            for sub in s[key]:
                e = []
                _validate(v, sub, root, path, e)
                ok.append(not e)
            if (key == "anyOf" and not any(ok)) or (key == "oneOf" and sum(ok) != 1):
                errs.append((path, f"不符合 {key} 的任何（或唯一）一種寫法"))
    for sub in s.get("allOf", []):
        _validate(v, sub, root, path, errs)
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v:
                errs.append((path, f"缺少必填欄位 {k}"))
        props = s.get("properties", {})
        for k, sub in props.items():
            if k in v:
                _validate(v[k], sub, root, path + (k,), errs)
        add = s.get("additionalProperties", True)
        for k in v:
            if k in props:
                continue
            if add is False:
                errs.append((path + (k,), "不允許的額外欄位"))
            elif isinstance(add, dict):
                _validate(v[k], add, root, path + (k,), errs)
    if isinstance(v, list):
        if "minItems" in s and len(v) < s["minItems"]:
            errs.append((path, f"至少要有 {s['minItems']} 筆"))
        if "maxItems" in s and len(v) > s["maxItems"]:
            errs.append((path, f"最多只能有 {s['maxItems']} 筆"))
        if "items" in s:
            for i, x in enumerate(v):
                _validate(x, s["items"], root, path + (i,), errs)


def check(doc, schema):
    if backend() == "jsonschema":
        v = jsonschema.Draft202012Validator(schema)
        out = []
        for e in v.iter_errors(doc):
            msg = e.message if len(e.message) <= 200 else e.message[:200] + "…"
            out.append((tuple(e.absolute_path), msg))
        return sorted(out, key=lambda x: [str(p) for p in x[0]])
    errs = []
    _validate(doc, schema, schema, (), errs)
    return errs
