"""每條新規則各一份最小 fixture：bad 會觸發、ok 不誤報（fixture 由 tests/fixtures/_build.py 產生）。"""
import unittest

from helper import fixture_lint, lint, rows, FIXTURES

WARN_RULES = ["V1", "V2", "F1", "F2", "F3", "F4"]
LEVEL = {"F3": "INFO"}   # F3 只提醒（代名詞歸屬不可靠，誤報多），其餘是 WARN


def lv(rule):
    return LEVEL.get(rule, "WARN")


class RuleTest(unittest.TestCase):
    def test_base_is_clean(self):
        code, out = fixture_lint("base", "ok")
        self.assertEqual(code, 0)
        self.assertEqual(rows(out, "WARN"), [])
        self.assertEqual(rows(out, "FAIL"), [])

    def test_x1_triggers_fail(self):
        code, out = fixture_lint("X1", "bad")
        self.assertEqual(code, 1)
        hits = rows(out, "FAIL", "X1")
        self.assertEqual(len(hits), 1, out)
        self.assertIn("shots.s001.status", hits[0])

    def test_x1_ok(self):
        code, out = fixture_lint("X1", "ok")
        self.assertEqual(code, 0)
        self.assertEqual(rows(out, code="X1"), [])

    def test_x1_not_in_legacy(self):
        code, out, _ = lint(FIXTURES / "X1" / "bad" / "plan", "--quiet", "--profile", "legacy")
        self.assertEqual(code, 0)
        self.assertEqual(rows(out, code="X1"), [])

    def test_warn_rules_trigger_exactly_once(self):
        for rule in WARN_RULES:
            with self.subTest(rule=rule):
                code, out = fixture_lint(rule, "bad")
                self.assertEqual(code, 0, out)                  # 只是 WARN，不擋
                self.assertEqual(len(rows(out, lv(rule), rule)), 1, out)

    def test_warn_rules_ok_no_false_positive(self):
        for rule in WARN_RULES:
            with self.subTest(rule=rule):
                code, out = fixture_lint(rule, "ok")
                self.assertEqual(code, 0, out)
                self.assertEqual(rows(out, lv(rule), rule), [], out)
                self.assertEqual(rows(out, "FAIL"), [], out)

    def test_exemptions_not_reported(self):
        for rule, case in (("F1", "ok_blink"), ("F2", "ok_vertical"), ("F2", "ok_noid"), ("F2", "ok_part"), ("F3", "ok_far"),
                           ("F3", "ok_pronoun"), ("F3", "ok_pronoun_prev"), ("F4", "ok_state")):
            with self.subTest(rule=rule, case=case):
                code, out = fixture_lint(rule, case)
                self.assertEqual(code, 0, out)
                self.assertEqual(rows(out, lv(rule), rule), [], out)

    def test_f3_pronoun_ambiguous_with_two_characters(self):
        _, out = fixture_lint("F3", "bad_two_chars")
        hits = rows(out, "INFO", "F3")
        self.assertEqual(len(hits), 1, out)
        self.assertIn("@hero", hits[0])

    def test_f4_vertical_word(self):
        _, out = fixture_lint("F4", "bad_vertical")
        self.assertEqual(len(rows(out, "WARN", "F4")), 1, out)

    def test_f1_state_arrow(self):
        code, out = fixture_lint("F1", "bad_arrow")
        self.assertEqual(len(rows(out, "WARN", "F1")), 1, out)
        self.assertIn("→", out)

    def test_new_rules_not_in_legacy(self):
        for rule in WARN_RULES:
            with self.subTest(rule=rule):
                _, out, _ = lint(FIXTURES / rule / "bad" / "plan", "--quiet", "--profile", "legacy")
                self.assertEqual(rows(out, lv(rule), rule), [])

    def test_f2_dict_facing_validated_against_vocab(self):
        """依階段的 facing：每個階段的值都得在 vocab.facing。"""
        import shutil, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "c"
            shutil.copytree(FIXTURES / "F2" / "ok", dst)
            shots = dst / "plan" / "shots.yaml"
            shots.write_text(shots.read_text(encoding="utf-8").replace("settled: to_camera", "settled: upside_down"), encoding="utf-8")
            code, out, _ = lint(dst / "plan", "--quiet")
            self.assertEqual(code, 1)
            self.assertTrue(any("facing.settled=upside_down" in l for l in rows(out, "FAIL", "S3")), out)

    def test_r2_aliases_list_itself_is_not_a_hit(self):
        """aliases_forbidden 清單本身不算使用別名；story 或 shots 真的用了才 FAIL。"""
        import shutil, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "c"
            shutil.copytree(FIXTURES / "base" / "ok", dst)
            gl = dst / "plan" / "glossary.yaml"
            gl.write_text(gl.read_text(encoding="utf-8").replace("kind: character", "aliases_forbidden: [女孩]\n    kind: character", 1), encoding="utf-8")
            code, out, _ = lint(dst / "plan", "--quiet")
            self.assertEqual(rows(out, "FAIL", "R2"), [], out)
            self.assertEqual(code, 0, out)
            st = dst / "plan" / "story.yaml"
            st.write_text(st.read_text(encoding="utf-8").replace("@hero 站在", "女孩站在", 1), encoding="utf-8")
            code, out, _ = lint(dst / "plan", "--quiet")
            self.assertEqual(code, 1)
            self.assertEqual(len(rows(out, "FAIL", "R2")), 1, out)

    def test_dict_facing_is_accepted_by_legacy_too(self):
        code, out, _ = lint(FIXTURES / "F2" / "ok" / "plan", "--quiet", "--profile", "legacy")
        self.assertEqual(code, 0, out)
        self.assertEqual(rows(out, "FAIL"), [])


if __name__ == "__main__":
    unittest.main()
