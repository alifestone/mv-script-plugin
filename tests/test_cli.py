"""CLI：任何工作目錄都能跑、timeline／labels／words 的預設與覆蓋。"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helper import EXAMPLE, FIXTURES, lint, rows, run


class CliTest(unittest.TestCase):
    def test_any_cwd(self):
        with tempfile.TemporaryDirectory() as d:
            a = lint(EXAMPLE / "plan", "--quiet", cwd=d)
        b = lint(EXAMPLE / "plan", "--quiet", cwd="/")
        self.assertEqual(a, b)
        self.assertEqual(a[0], 0)

    def test_relative_plan_path(self):
        code, out, _ = lint("plan", "--quiet", cwd=EXAMPLE)    # 相對路徑：timeline 以 plan 的上一層解析
        self.assertEqual(code, 0)
        self.assertIn("鏡頭覆蓋到 66.00 s", out)

    def test_timeline_override(self):
        with tempfile.TemporaryDirectory() as d:
            tl = Path(d) / "elsewhere.json"
            shutil.copy(EXAMPLE / "analysis" / "timeline.json", tl)
            plan = Path(d) / "p"
            shutil.copytree(EXAMPLE / "plan", plan)
            code, out, _ = lint(plan, "--quiet", "--timeline", tl)          # 上一層沒有 analysis/，靠 --timeline
            self.assertEqual(code, 0, out)
            code, _, err = lint(plan, "--quiet")                            # 沒給也找不到
            self.assertNotEqual(code, 0)

    def test_missing_timeline_field(self):
        with tempfile.TemporaryDirectory() as d:
            plan = Path(d) / "p"
            shutil.copytree(FIXTURES / "base" / "ok" / "plan", plan)
            proj = plan / "project.yaml"
            proj.write_text("\n".join(l for l in proj.read_text(encoding="utf-8").splitlines() if not l.startswith("timeline")) + "\n", encoding="utf-8")
            code, _, err = lint(plan, "--quiet")
            self.assertNotEqual(code, 0)
            self.assertIn("--timeline", err)

    def test_words_override_and_missing_keys(self):
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "w.yaml"
            w.write_text("vague_words: [氣氛]\n", encoding="utf-8")
            code, out, err = lint(FIXTURES / "V2" / "bad" / "plan", "--quiet", "--words", w)
            self.assertEqual(rows(out, code="V2"), [])       # 沒有 metaphor_words → 規則略過
            self.assertIn("缺少", err)

    def test_render_without_labels_shows_raw_keys(self):
        with tempfile.TemporaryDirectory() as d:
            plan = Path(d) / "plan"
            shutil.copytree(EXAMPLE / "plan", plan, ignore=shutil.ignore_patterns("labels.yaml"))   # <plan>/labels.yaml 不存在
            out = Path(d) / "x" / "mv.md"                     # 父目錄不存在也會建
            code, stdout, _ = run("render_plan.py", "--plan", plan, "--timeline", EXAMPLE / "analysis" / "timeline.json", "--out", out)
            self.assertEqual(code, 0)
            md = out.read_text(encoding="utf-8")
            self.assertIn("| shape |", md)
            self.assertNotIn("| 形狀 |", md)
            self.assertIn("由 plan 目錄的 YAML 以 render_plan.py 產生", md)

    def test_render_default_labels_and_out(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            shutil.copytree(EXAMPLE / "plan", root / "plan")          # 含 plan/labels.yaml
            (root / "analysis").mkdir()
            shutil.copy(EXAMPLE / "analysis" / "timeline.json", root / "analysis" / "timeline.json")
            code, _, _ = run("render_plan.py", "--plan", root / "plan", cwd="/")
            self.assertEqual(code, 0)
            md = (root / "docs" / "mv_plan.md").read_bytes()    # 預設 <plan 上一層>/docs/mv_plan.md
            self.assertEqual(md, (EXAMPLE / "docs" / "mv_plan.md").read_bytes())

    def test_render_dict_facing(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "mv.md"
            run("render_plan.py", "--plan", FIXTURES / "F2" / "ok" / "plan", "--out", out)
            self.assertIn("面向 entering：away；settled：to_camera", out.read_text(encoding="utf-8"))

    def test_templates_labels_is_valid_yaml(self):
        import yaml
        from helper import ROOT
        d = yaml.safe_load((ROOT / "skills" / "mv-script" / "templates" / "labels.yaml").read_text(encoding="utf-8"))
        self.assertIn("fields", d)


if __name__ == "__main__":
    unittest.main()
