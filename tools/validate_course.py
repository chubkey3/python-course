"""
Validate the whole course the way PrairieLearn's sync would (and then some).

    python tools/validate_course.py

Checks:
  - every infoCourse / infoCourseInstance / infoAssessment / info.json against PrairieLearn's
    JSON Schemas (copied into tools/schemas/; needs `pip install jsonschema`)
  - UUIDs are unique across the whole course
  - question topics/tags exist in infoCourse.json; assessment sets exist
  - every question ID referenced by an assessment exists
  - Exam autoPoints lists are non-increasing; Homework autoPoints is a single number;
    time limits (durationMinutes) only on Exam-type assessments
  - workspace questions use singleVariant; judge questions have a valid tests/cases.json
    and a student file the judge can find
  - CRLF line endings in files that run on Linux
Exits 1 if there are errors. Warnings don't fail.
"""

import json
import re
import sys
from pathlib import Path

COURSE = Path(__file__).resolve().parent.parent
SCHEMAS = Path(__file__).resolve().parent / "schemas"
JUDGE_ENTRYPOINT = "/grade/serverFilesCourse/judge/run.sh"

STANDARD_SETS = {"Homework", "Machine Problem", "Quiz", "Practice Quiz", "Exam", "Practice Exam", "Prep", "Worksheet"}
STANDARD_TAGS = {
    "numeric", "symbolic", "drawing", "MC", "code", "multianswer", "graph", "concept", "calculate",
    "compute", "software", "estimation", "secret", "nontest",
}

errors: list[str] = []
warnings: list[str] = []


def rel(p: Path) -> str:
    return str(p.relative_to(COURSE)).replace("\\", "/")


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{rel(p)}: invalid JSON: {e}")
        return None


def schema_check(p: Path, data, schema_name: str) -> None:
    try:
        import jsonschema
    except ImportError:
        if not getattr(schema_check, "warned", False):
            warnings.append("jsonschema not installed; skipping schema validation (pip install jsonschema)")
            schema_check.warned = True
        return
    schema = json.loads((SCHEMAS / f"{schema_name}.json").read_text(encoding="utf-8"))
    validator = jsonschema.validators.validator_for(schema)(schema)
    for err in validator.iter_errors(data):
        loc = "/".join(str(x) for x in err.path) or "(root)"
        errors.append(f"{rel(p)}: schema: {loc}: {err.message[:300]}")


uuids: dict[str, str] = {}


def register_uuid(p: Path, data) -> None:
    u = (data or {}).get("uuid")
    if not u:
        return
    key = u.lower()
    if key in uuids:
        errors.append(f"{rel(p)}: duplicate uuid {u} (also used by {uuids[key]})")
    else:
        uuids[key] = rel(p)


def check_line_endings(paths) -> None:
    for p in paths:
        if p.is_file() and b"\r\n" in p.read_bytes():
            errors.append(f"{rel(p)}: CRLF line endings (must be LF; this file runs on Linux)")


# ---------- course ----------
course_path = COURSE / "infoCourse.json"
course = load_json(course_path) or {}
schema_check(course_path, course, "infoCourse")
topics = {t["name"] for t in course.get("topics", [])}
tags = {t["name"] for t in course.get("tags", [])} | STANDARD_TAGS
sets = {s["name"] for s in course.get("assessmentSets", [])} | STANDARD_SETS

check_line_endings(list((COURSE / "serverFilesCourse").rglob("*")))

# ---------- questions ----------
question_ids: set[str] = set()
for info_path in sorted((COURSE / "questions").rglob("info.json")):
    qdir = info_path.parent
    qid = rel(qdir).removeprefix("questions/")
    question_ids.add(qid)
    info = load_json(info_path)
    if info is None:
        continue
    schema_check(info_path, info, "infoQuestion")
    register_uuid(info_path, info)

    if info.get("topic") not in topics:
        errors.append(f"{rel(info_path)}: topic {info.get('topic')!r} is not defined in infoCourse.json")
    for t in info.get("tags", []):
        if t not in tags:
            errors.append(f"{rel(info_path)}: tag {t!r} is not defined in infoCourse.json")

    html_path = qdir / "question.html"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    if not html:
        errors.append(f"{qid}: missing or empty question.html")
    if "{{" in html and not (qdir / "server.py").exists():
        warnings.append(f"{qid}: question.html contains '{{{{' but there is no server.py (Mustache will try to render it)")

    if "workspaceOptions" in info:
        if not info.get("singleVariant"):
            errors.append(f"{qid}: workspace questions must set \"singleVariant\": true")
        if "<pl-workspace" not in html:
            errors.append(f"{qid}: has workspaceOptions but question.html has no <pl-workspace>")

    ego = info.get("externalGradingOptions") or {}
    if info.get("gradingMethod") == "External":
        if "<pl-external-grader-results" not in html:
            warnings.append(f"{qid}: external grading but no <pl-external-grader-results> in question.html")
    if ego.get("entrypoint") == JUDGE_ENTRYPOINT:
        if "judge/" not in ego.get("serverFilesCourse", []):
            errors.append(f"{qid}: judge entrypoint requires externalGradingOptions.serverFilesCourse: [\"judge/\"]")
        if ego.get("image") != "prairielearn/grader-python":
            errors.append(f"{qid}: the judge needs externalGradingOptions.image \"prairielearn/grader-python\"")
        cases_path = qdir / "tests" / "cases.json"
        check_line_endings(list((qdir / "tests").rglob("*")) + list((qdir / "workspace").rglob("*")))
        cases = load_json(cases_path) if cases_path.exists() else None
        if cases is None:
            errors.append(f"{qid}: judge question is missing a valid tests/cases.json")
        else:
            student_file = cases.get("studentFile", "main.py")
            cs = cases.get("cases", [])
            if not cs:
                errors.append(f"{qid}: tests/cases.json has no cases")
            for i, c in enumerate(cs, 1):
                if "input" not in c or "output" not in c:
                    errors.append(f"{qid}: case {i} needs both 'input' and 'output'")
                elif c["output"] == "":
                    warnings.append(f"{qid}: case {i} has empty expected output (forgot check_question.py --fix?)")
            if not any(c.get("hidden") is False for c in cs):
                warnings.append(f"{qid}: no visible sample cases (\"hidden\": false)")
            if not any(c.get("hidden", True) for c in cs):
                warnings.append(f"{qid}: no hidden test cases")
            graded = (info.get("workspaceOptions") or {}).get("gradedFiles", [])
            # \s (not \b) so this doesn't match inside source-file-name="..."
            editor_names = re.findall(r'<pl-file-editor[^>]*?\sfile-name="([^"]+)"', html)
            if student_file not in graded and student_file not in editor_names:
                errors.append(
                    f"{qid}: judge expects {student_file!r} but it is neither in workspaceOptions.gradedFiles "
                    f"nor a <pl-file-editor file-name=...>"
                )
            if not (qdir / "tests" / "solution.py").exists():
                warnings.append(f"{qid}: no tests/solution.py (expected outputs can't be checked)")
            if "BEGIN SAMPLES" not in html:
                warnings.append(f"{qid}: question.html has no BEGIN/END SAMPLES block (samples won't auto-sync)")

# ---------- course instances & assessments ----------
for ci_path in sorted((COURSE / "courseInstances").rglob("infoCourseInstance.json")):
    ci = load_json(ci_path)
    schema_check(ci_path, ci, "infoCourseInstance")
    register_uuid(ci_path, ci)
    labels: dict[tuple, str] = {}
    for a_path in sorted((ci_path.parent / "assessments").rglob("infoAssessment.json")):
        a = load_json(a_path)
        if a is None:
            continue
        schema_check(a_path, a, "infoAssessment")
        register_uuid(a_path, a)
        name = rel(a_path)
        if a.get("set") not in sets:
            errors.append(f"{name}: set {a.get('set')!r} is not a defined or standard assessment set")
        key = (a.get("set"), str(a.get("number")))
        if key in labels:
            errors.append(f"{name}: set+number {key} duplicates {labels[key]}")
        labels[key] = name
        atype = a.get("type")
        for rule in a.get("accessControl", []) or []:
            if (rule.get("dateControl") or {}).get("durationMinutes") and atype != "Exam":
                errors.append(f"{name}: time limits (durationMinutes) are only supported on Exam-type assessments")
        if a.get("accessControl") and (a["accessControl"][0].get("dateControl") or {}) and not a["accessControl"][0]["dateControl"].get("release"):
            errors.append(f"{name}: defaults rule with dateControl needs a release date")
        seen_ids: set[str] = set()
        for zi, zone in enumerate(a.get("zones", []), 1):
            for slot in zone.get("questions", []):
                entries = slot.get("alternatives") or [slot]
                for q in entries:
                    qid = q.get("id")
                    if qid is None:
                        continue
                    if qid.startswith("@"):
                        continue  # shared question from another course
                    if qid not in question_ids:
                        errors.append(f"{name}: zone {zi}: question {qid!r} does not exist")
                    if qid in seen_ids:
                        errors.append(f"{name}: question {qid!r} appears more than once")
                    seen_ids.add(qid)
                    pts = q.get("autoPoints", slot.get("autoPoints", q.get("points", slot.get("points"))))
                    if atype == "Homework" and isinstance(pts, list):
                        errors.append(f"{name}: {qid}: Homework autoPoints must be a single number, not a list")
                    if atype == "Exam" and isinstance(pts, list) and any(x < y for x, y in zip(pts, pts[1:])):
                        errors.append(f"{name}: {qid}: Exam autoPoints must be non-increasing")
        if not seen_ids:
            warnings.append(f"{name}: assessment has no questions")

for w in warnings:
    print(f"WARNING: {w}")
for e in errors:
    print(f"ERROR:   {e}")
print(f"\n{len(question_ids)} questions, {len(uuids)} uuids checked: {len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
