"""測試共用：用子行程呼叫 scripts/ 下的 CLI（絕對路徑，與工作目錄無關）。"""
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
SCRIPTS = ROOT / "skills" / "mv-script" / "scripts"
EXAMPLE = ROOT / "examples" / "neon-courier"   # 完整範例（虛構）；測試以它為基準
SNAPSHOTS = TESTS / "golden" / "example"        # 範例的 lint 快照
FIXTURES = TESTS / "fixtures"


def run(script, *args, cwd=None):
    """執行 scripts/<script>；回傳 (結束碼, stdout, stderr)，stdout 保留原始位元組解碼。"""
    p = subprocess.run([sys.executable, "-B", str(SCRIPTS / script), *map(str, args)],
                       capture_output=True, cwd=cwd, check=False)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def lint(plan, *args, cwd=None):
    return run("lint_plan.py", "--plan", plan, *args, cwd=cwd)


def fixture_lint(rule, case):
    """跑 tests/fixtures/<rule>/<case>/plan（--quiet），回傳 (結束碼, stdout)。"""
    code, out, _ = lint(FIXTURES / rule / case / "plan", "--quiet")
    return code, out


def rows(out, level=None, code=None):
    """stdout 裡符合層級與代碼的行。"""
    res = []
    for line in out.splitlines():
        if line.startswith("FAIL ") and "  WARN " in line:    # 摘要行（FAIL n  WARN n  OPEN n）
            continue
        parts = line.split(" ", 2) if not line.startswith(("WARN", "FAIL", "INFO", "OPEN")) else line.split(None, 2)
        if len(parts) >= 2 and (level is None or parts[0] == level) and (code is None or parts[1] == code):
            res.append(line)
    return res
