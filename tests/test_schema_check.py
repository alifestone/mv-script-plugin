"""內建 JSON Schema 驗證器（子集）；以及 schema 檔本身只用得到這個子集。"""
import json
import os
import unittest

import sys
from helper import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
os.environ["MV_SCHEMA_BUILTIN"] = "1"
import schema_check  # noqa: E402


class BuiltinValidatorTest(unittest.TestCase):
    S = {"type": "object", "required": ["a"], "properties": {
        "a": {"enum": ["x", "y"]},
        "n": {"type": ["integer", "null"], "minimum": 0},
        "l": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"$ref": "#/$defs/num"}},
        "u": {"anyOf": [{"type": "string"}, {"type": "object", "additionalProperties": {"type": "string"}}]},
    }, "$defs": {"num": {"type": "number"}}}

    def errs(self, doc):
        return schema_check.check(doc, self.S)

    def test_ok(self):
        self.assertEqual(self.errs({"a": "x", "n": None, "l": [1, 2.5], "u": {"k": "v"}, "extra": 1}), [])

    def test_required_and_enum(self):
        self.assertEqual([m for _, m in self.errs({})], ["缺少必填欄位 a"])
        self.assertEqual(self.errs({"a": "z"})[0][0], ("a",))

    def test_types_and_bool_not_integer(self):
        self.assertEqual(self.errs({"a": "x", "n": True})[0][0], ("n",))
        self.assertEqual(self.errs({"a": "x", "n": -1})[0][0], ("n",))

    def test_items_ref_and_length(self):
        e = self.errs({"a": "x", "l": [1, "no"]})
        self.assertEqual([p for p, _ in e], [("l", 1)])
        self.assertEqual(len(self.errs({"a": "x", "l": [1]})), 1)

    def test_anyof(self):
        self.assertEqual(len(self.errs({"a": "x", "u": 5})), 1)
        self.assertEqual(self.errs({"a": "x", "u": "s"}), [])

    def test_additional_properties_false(self):
        s = {"type": "object", "properties": {"a": {}}, "additionalProperties": False}
        self.assertEqual(schema_check.check({"a": 1, "b": 2}, s)[0][0], ("b",))


class SchemaFilesTest(unittest.TestCase):
    ALLOWED = {"$schema", "$defs", "$ref", "title", "description", "type", "enum", "const", "required", "properties",
               "items", "additionalProperties", "anyOf", "oneOf", "allOf", "minItems", "maxItems", "minimum", "minLength"}

    def test_only_supported_keywords(self):
        def walk(node, where):
            if isinstance(node, dict):
                for k, v in node.items():
                    in_props = where.endswith(("properties", "$defs"))
                    if not in_props:
                        self.assertIn(k, self.ALLOWED, f"{where}.{k} 內建驗證器不支援")
                    walk(v, f"{where}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{where}[{i}]")
        for name in schema_check.SCHEMA_NAMES:
            walk(schema_check.load_schema(schema_check.DEFAULT_DIR, name), name)

    def test_schema_files_are_valid_json(self):
        for name in schema_check.SCHEMA_NAMES:
            p = schema_check.DEFAULT_DIR / f"{name}.schema.json"
            json.loads(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
