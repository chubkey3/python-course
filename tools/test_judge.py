"""
End-to-end test of judge-graded questions inside the real prairielearn/grader-python image.

    python tools/test_judge.py questions/loops-and-lists/factorial [more question dirs...]
    python tools/test_judge.py --all

For each question whose grader is the course judge, it builds a /grade job directory exactly
like PrairieLearn does and runs the judge in Docker:
  - tests/solution.py           must score 100%
  - the starter code            must score below 100% (it shouldn't already solve the problem)
  - a probe that tries to read /grade/tests/cases.json must NOT leak it
Requires Docker to be running. Exits 1 on any failure, 2 if Docker isn't available.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COURSE = Path(__file__).resolve().parent.parent
IMAGE = "prairielearn/grader-python"
JUDGE_ENTRYPOINT = "/grade/serverFilesCourse/judge/run.sh"
LEAK_PROBE = "print(open('/grade/tests/cases.json').read())\nprint(open('/grade/tests/solution.py').read())\n"


def is_judge_question(qdir: Path) -> bool:
    info_path = qdir / "info.json"
    if not info_path.exists():
        return False
    info = json.loads(info_path.read_text(encoding="utf-8"))
    return (info.get("externalGradingOptions") or {}).get("entrypoint") == JUDGE_ENTRYPOINT


def find_starter(qdir: Path, student_file: str) -> str | None:
    ws = qdir / "workspace" / student_file
    if ws.exists():
        return ws.read_text(encoding="utf-8")
    html = (qdir / "question.html").read_text(encoding="utf-8")
    m = re.search(r"<pl-file-editor\b([^>]*)>(.*?)</pl-file-editor>", html, re.S)
    if m:
        src = re.search(r'source-file-name="([^"]+)"', m.group(1))
        if src:
            d = re.search(r'directory="([^"]+)"', m.group(1))
            base = qdir / d.group(1) if d else qdir
            return (base / src.group(1)).read_text(encoding="utf-8")
        return m.group(2)
    return None


def grade(qdir: Path, student_file: str, code: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "grade"
        shutil.copytree(qdir / "tests", g / "tests")
        shutil.copytree(COURSE / "serverFilesCourse" / "judge", g / "serverFilesCourse" / "judge")
        (g / "student").mkdir()
        (g / "student" / student_file).write_text(code, encoding="utf-8", newline="\n")
        (g / "data").mkdir()
        (g / "data" / "data.json").write_text('{"params": {}}', encoding="utf-8")
        out = Path(tmp) / "out"
        out.mkdir()
        script = (
            "cp -r /grade_src /grade && chmod +x /grade/serverFilesCourse/judge/run.sh && "
            "/grade/serverFilesCourse/judge/run.sh; cp /grade/results/results.json /out/ 2>/dev/null; true"
        )
        r = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "-v", f"{g}:/grade_src:ro", "-v", f"{out}:/out",
             "--entrypoint", "bash", IMAGE, "-c", script],
            capture_output=True, text=True, timeout=600,
        )
        res = out / "results.json"
        if not res.exists():
            return {"_error": (r.stdout + r.stderr)[-1500:]}
        return json.loads(res.read_text(encoding="utf-8"))


def describe(res: dict) -> str:
    if "_error" in res:
        return "NO RESULTS: " + res["_error"]
    if not res.get("gradable", True):
        return "not gradable: " + res.get("message", "").splitlines()[0]
    failed = [f"{t['name']}: {t['message']}" for t in res["tests"] if t["points"] < t["max_points"]]
    return f"score {res['score']:.0%} ({res['message']})" + (f" first failure -> {failed[0]}" if failed else "")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        dirs = sorted(p.parent for p in (COURSE / "questions").rglob("info.json"))
    else:
        dirs = [Path(a).resolve() for a in args]
    dirs = [d for d in dirs if is_judge_question(d)]
    if not dirs:
        print("No judge-graded questions to test.")
        return
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        print("Docker is not running. Start Docker Desktop and re-run.")
        sys.exit(2)

    ok = True
    for qdir in dirs:
        name = str(qdir.relative_to(COURSE / "questions")).replace("\\", "/")
        cases = json.loads((qdir / "tests" / "cases.json").read_text(encoding="utf-8"))
        student_file = cases.get("studentFile", "main.py")

        sol_path = qdir / "tests" / "solution.py"
        if sol_path.exists():
            r = grade(qdir, student_file, sol_path.read_text(encoding="utf-8"))
            passed = r.get("score") == 1.0
            ok &= passed
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: solution -> {describe(r)}")
        else:
            print(f"[SKIP] {name}: no tests/solution.py")

        starter = find_starter(qdir, student_file)
        if starter is not None and starter.strip():
            r = grade(qdir, student_file, starter)
            passed = r.get("score", 0) < 1.0
            ok &= passed
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: starter -> {describe(r)}"
                  + ("" if passed else "  (starter code already solves the problem!)"))

        r = grade(qdir, student_file, LEAK_PROBE)
        outputs = " ".join(t.get("output", "") for t in r.get("tests", []))
        leaked = '"cases"' in outputs or (sol_path.exists() and sol_path.read_text(encoding="utf-8").strip()[:40] in outputs)
        ok &= not leaked
        print(f"[{'FAIL' if leaked else 'PASS'}] {name}: hidden tests {'LEAKED to student code!' if leaked else 'not readable by student code'}")

    print("\nALL JUDGE TESTS PASSED" if ok else "\nSOME JUDGE TESTS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
