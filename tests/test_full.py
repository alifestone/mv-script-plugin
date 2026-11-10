"""以 examples/neon-courier 為基準：full profile 必須 FAIL 0、WARN 0，lint 輸出與 render 產物都與快照逐位元組相同。
更新快照與範例文件：UPDATE_SNAPSHOT=1 python3 -m unittest discover tests"""
import os
import tempfile
import unittest
from pathlib import Path

from helper import EXAMPLE, SNAPSHOTS, lint, rows, run

LINT_SNAPSHOT = SNAPSHOTS / "lint.txt"
RENDER_SNAPSHOT = EXAMPLE / "docs" / "mv_plan.md"
NEW_CODES = {"X1", "V1", "V2", "F1", "F2", "F3", "F4"}
UPDATE = bool(os.environ.get("UPDATE_SNAPSHOT"))


class ExampleTest(unittest.TestCase):
    def test_lint_no_fail_no_warn_and_snapshot(self):
        code, out, _ = lint(EXAMPLE / "plan")                 # 預設就是 full
        self.assertEqual(code, 0, out)
        self.assertEqual(rows(out, "FAIL"), [])
        self.assertEqual(rows(out, "WARN"), [], out)
        self.assertEqual(rows(out, code="X1"), [])
        if UPDATE:
            LINT_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
            LINT_SNAPSHOT.write_text(out, encoding="utf-8")
        self.assertEqual(out.encode(), LINT_SNAPSHOT.read_bytes())

    def test_lint_shows_open_items_but_quiet_hides_them(self):
        _, out, _ = lint(EXAMPLE / "plan")
        _, quiet, _ = lint(EXAMPLE / "plan", "--quiet")
        self.assertTrue(rows(out, "OPEN", "P1"))              # proposed
        self.assertTrue(rows(out, "OPEN", "Q1"))              # shots.s013 的 questions
        self.assertTrue(rows(out, "OPEN", "Q2"))              # review/intro_r1.yaml 裡 status: open 的題
        self.assertEqual(rows(quiet, "OPEN"), [])
        self.assertTrue(rows(quiet, "INFO", "T6"))

    def test_render_matches_example_doc(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "mv_plan.md"
            code, stdout, _ = run("render_plan.py", "--plan", EXAMPLE / "plan", "--out", out)   # 預設讀 <plan>/labels.yaml
            self.assertEqual(code, 0)
            self.assertTrue(stdout.startswith(f"寫入 {out}（"), stdout)
            if UPDATE:
                RENDER_SNAPSHOT.write_bytes(out.read_bytes())
            self.assertEqual(out.read_bytes(), RENDER_SNAPSHOT.read_bytes())

    def test_legacy_profile_runs_clean(self):
        code, out, _ = lint(EXAMPLE / "plan", "--profile", "legacy")
        self.assertEqual(code, 0, out)
        self.assertEqual(rows(out, "FAIL"), [])
        self.assertEqual(rows(out, "WARN"), [])

    def test_full_is_legacy_plus_new_rules(self):
        """full 的輸出扣掉新代碼的列，必須等於 legacy。"""
        _, full, _ = lint(EXAMPLE / "plan")
        _, legacy, _ = lint(EXAMPLE / "plan", "--profile", "legacy")
        keep = [l for l in full.splitlines() if not (l.startswith(("WARN", "INFO")) and l.split()[1] in NEW_CODES)]
        self.assertEqual(keep, legacy.splitlines())

    def test_default_profile_is_full(self):
        self.assertEqual(lint(EXAMPLE / "plan")[1], lint(EXAMPLE / "plan", "--profile", "full")[1])

    def test_example_covers_the_documented_features(self):
        """範例要示範的東西都在：route、variation、轉場、dict facing、no_face、read_as、model_hint、questions、兩種 status。"""
        import yaml
        shots = yaml.safe_load((EXAMPLE / "plan" / "shots.yaml").read_text(encoding="utf-8"))["shots"]
        gloss = yaml.safe_load((EXAMPLE / "plan" / "glossary.yaml").read_text(encoding="utf-8"))["entities"]
        self.assertTrue(10 <= len(shots) <= 14)
        self.assertEqual({s["route"] for s in shots}, {"A", "B", "C"})
        self.assertEqual({s["variation"] for s in shots}, {"small", "medium", "large"})
        self.assertGreaterEqual(len({s["transition_in"]["type"] for s in shots}), 6)
        self.assertEqual({s["status"] for s in shots}, {"proposed", "confirmed"})
        self.assertTrue(any(isinstance(x.get("facing"), dict) for s in shots for x in s["subjects"]))
        self.assertTrue(any(s.get("read_as") for s in shots))
        self.assertTrue(any(s.get("model_hint") for s in shots))
        self.assertTrue(any(s.get("questions") for s in shots))
        self.assertTrue(any(e.get("no_face") for e in gloss.values()))
        self.assertEqual(sorted(e["kind"] for e in gloss.values()),
                         ["character", "character", "object", "place", "place", "vfx"])
        for e in gloss.values():
            self.assertTrue(e.get("not_this") and e.get("refs") and e.get("look") is not None, e["name"])


if __name__ == "__main__":
    unittest.main()
