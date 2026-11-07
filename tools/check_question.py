"""
Authoring helper for stdin/stdout questions (runs locally, not on PrairieLearn).

Runs a question's reference solution (tests/solution.py) against every case in
tests/cases.json and reports any case whose expected output doesn't match.

Usage:
    python tools/check_question.py questions/loops-and-lists/factorial
    python tools/check_question.py questions/loops-and-lists/factorial --fix   # (re)write expected outputs from the solution
    python tools/check_question.py --all [--fix]                               # every question that has tests/cases.json

Uses the same comparison modes as serverFilesCourse/judge/judge.py.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

COURSE_DIR = Path(__file__).resolve().parent.parent


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


def check(question_dir: Path, fix: bool) -> bool:
    cases_path = question_dir / "tests" / "cases.json"
    solution = question_dir / "tests" / "solution.py"
    if not solution.is_file():
        print(f"[skip] {question_dir}: no tests/solution.py")
        return True
    config = json.loads(cases_path.read_text(encoding="utf-8"))
    mode = config.get("compare", "tokens")
    timeout = float(config.get("timeoutSeconds", 2))
    ok = True
    for i, case in enumerate(config["cases"], start=1):
        name = case.get("name", f"Test {i}")
        result = subprocess.run(
            [sys.executable, str(solution)],
            input=case.get("input", ""),
            capture_output=True,
            text=True,
            timeout=timeout * 5,
        )
        if result.returncode != 0:
            print(f"[FAIL] {question_dir.name} / {name}: solution crashed\n{result.stderr}")
            ok = False
            continue
        if fix:
            case["output"] = result.stdout
        elif normalize(result.stdout, mode) != normalize(case.get("output", ""), mode):
            print(f"[FAIL] {question_dir.name} / {name}: expected {case.get('output')!r}, solution printed {result.stdout!r}")
            ok = False
    if fix:
        cases_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"[fixed] {question_dir.relative_to(COURSE_DIR)}: wrote {len(config['cases'])} expected outputs")
    elif ok:
        print(f"[ok] {question_dir.relative_to(COURSE_DIR)}: {len(config['cases'])} cases match")
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
