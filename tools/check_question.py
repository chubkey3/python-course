"""
Authoring helper for stdin/stdout questions (runs locally, not on PrairieLearn).

Runs a question's reference solution (tests/solution.py) against every case in
tests/cases.json and reports any case whose expected output doesn't match.

With --fix it instead:
  1. (re)writes every case's expected "output" from the solution, and
  2. regenerates the samples block in question.html (between the
     <!-- BEGIN SAMPLES ... --> and <!-- END SAMPLES --> markers) from the
     visible ("hidden": false) cases, including each case's optional "explanation".

Usage:
    python tools/check_question.py questions/loops-and-lists/factorial
    python tools/check_question.py questions/loops-and-lists/factorial --fix
    python tools/check_question.py --all [--fix]      # every question that has tests/cases.json

Uses the same comparison modes as serverFilesCourse/judge/judge.py.
"""

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

COURSE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_RE = re.compile(r"([ \t]*<!-- BEGIN SAMPLES[^>]*-->\n)(.*?)([ \t]*<!-- END SAMPLES -->)", re.S)


def normalize(text: str, mode: str):
    text = text.replace("\r\n", "\n")
    if mode == "exact":
        return text
    if mode == "lines":
        lines = [line.rstrip() for line in text.split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        return lines
    return text.split()


def render_samples(cases: list[dict]) -> str:
    parts = []
    for i, c in enumerate([c for c in cases if c.get("hidden", True) is False], start=1):
        parts.append(
            f"  <p><strong>Sample input {i}</strong></p>\n"
            f"  <pl-code copy-code-button=\"true\">{html.escape(c['input'].rstrip())}</pl-code>"
        )
        parts.append(f"  <p><strong>Sample output {i}</strong></p>\n  <pre>{html.escape(c['output'].rstrip())}</pre>")
        if c.get("explanation"):
            parts.append(f"  <p>{c['explanation']}</p>")
    return "\n".join(parts) + "\n"


def check(question_dir: Path, fix: bool) -> bool:
    cases_path = question_dir / "tests" / "cases.json"
    solution = question_dir / "tests" / "solution.py"
    name = str(question_dir.relative_to(COURSE_DIR)).replace("\\", "/")
    if not solution.is_file():
        print(f"[skip] {name}: no tests/solution.py")
        return True
    config = json.loads(cases_path.read_text(encoding="utf-8"))
    mode = config.get("compare", "tokens")
    timeout = float(config.get("timeoutSeconds", 2))
    ok = True
    for i, case in enumerate(config["cases"], start=1):
        case_name = case.get("name", f"Test {i}")
        try:
            result = subprocess.run(
                [sys.executable, str(solution)],
                input=case.get("input", ""),
                capture_output=True,
                text=True,
                timeout=timeout * 5,
            )
        except subprocess.TimeoutExpired:
            print(f"[FAIL] {name} / {case_name}: solution timed out (>{timeout * 5:g}s)")
            ok = False
            continue
        if result.returncode != 0:
            print(f"[FAIL] {name} / {case_name}: solution crashed\n{result.stderr}")
            ok = False
            continue
        if fix:
            case["output"] = result.stdout
        elif normalize(result.stdout, mode) != normalize(case.get("output", ""), mode):
            print(f"[FAIL] {name} / {case_name}: expected {case.get('output')!r}, solution printed {result.stdout!r}")
            ok = False

    html_path = question_dir / "question.html"
    page = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    m = SAMPLES_RE.search(page)
    if fix and ok:
        cases_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
        msg = f"wrote {len(config['cases'])} expected outputs"
        if m:
            page = page[: m.start(2)] + render_samples(config["cases"]) + page[m.end(2):]
            html_path.write_text(page, encoding="utf-8", newline="\n")
            msg += " and regenerated the question.html samples"
        visible = [c for c in config["cases"] if c.get("hidden", True) is False]
        if (question_dir / "workspace").is_dir() and visible:
            (question_dir / "workspace" / "sample_input.txt").write_text(visible[0]["input"], encoding="utf-8", newline="\n")
            msg += " and workspace/sample_input.txt"
        print(f"[fixed] {name}: {msg}")
    elif ok:
        if m and m.group(2) != render_samples(config["cases"]):
            print(f"[FAIL] {name}: question.html samples are out of date with tests/cases.json (run with --fix)")
            ok = False
        else:
            print(f"[ok] {name}: {len(config['cases'])} cases match")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question_dirs", nargs="*", type=Path)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    dirs = [d.resolve() for d in args.question_dirs]
    if args.all:
        dirs = sorted(p.parent.parent for p in (COURSE_DIR / "questions").rglob("tests/cases.json"))
    if not dirs:
        parser.error("give one or more question directories, or --all")
    results = [check(d, args.fix) for d in dirs]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
