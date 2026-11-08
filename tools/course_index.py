"""
Print an overview of the course: the question bank and every assessment.

    python tools/course_index.py            # human-readable
    python tools/course_index.py --json     # machine-readable

For each question: ID, title, topic, tags, format, and which assessments use it.
For each assessment: label (e.g. HW2), type, title, question count, access summary.
Also prints the next free number for each assessment set.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

COURSE = Path(__file__).resolve().parent.parent
JUDGE_ENTRYPOINT = "/grade/serverFilesCourse/judge/run.sh"


def question_format(info: dict, html: str) -> str:
    judge = (info.get("externalGradingOptions") or {}).get("entrypoint") == JUDGE_ENTRYPOINT
    if "workspaceOptions" in info:
        return "workspace-stdio" if judge else "workspace"
    if "<pl-file-editor" in html:
        return "editor-stdio" if judge else "editor"
    elements = sorted(set(re.findall(r"<(pl-[a-z-]+-input|pl-multiple-choice|pl-checkbox|pl-order-blocks|pl-matching)\b", html)))
    return "+".join(e.removeprefix("pl-") for e in elements) or "other"


def main() -> None:
    course = json.loads((COURSE / "infoCourse.json").read_text(encoding="utf-8"))
    abbrev = {s["name"]: s["abbreviation"] for s in course.get("assessmentSets", [])}
    abbrev.update({k: v for k, v in {"Homework": "HW", "Quiz": "Q", "Exam": "E", "Practice Quiz": "PQ", "Practice Exam": "PE", "Machine Problem": "MP", "Prep": "P", "Worksheet": "WS"}.items() if k not in abbrev})

    assessments = []
    used_in = defaultdict(list)
    numbers = defaultdict(list)
    for a_path in sorted((COURSE / "courseInstances").rglob("infoAssessment.json")):
        a = json.loads(a_path.read_text(encoding="utf-8"))
        instance = a_path.relative_to(COURSE / "courseInstances").parts[0]
        label = f"{abbrev.get(a.get('set'), a.get('set'))}{a.get('number')}"
        qids = []
        for zone in a.get("zones", []):
            for slot in zone.get("questions", []):
                for q in slot.get("alternatives") or [slot]:
                    if q.get("id"):
                        qids.append(q["id"])
                        used_in[q["id"]].append(label)
        dc = ((a.get("accessControl") or [{}])[0] or {}).get("dateControl") or {}
        access = []
        if dc.get("release"):
            access.append(f"release {dc['release'].get('date')}")
        if dc.get("due"):
            access.append(f"due {dc['due'].get('date') or 'none'}")
        if dc.get("durationMinutes"):
            access.append(f"{dc['durationMinutes']} min")
        if dc.get("password"):
            access.append("password")
        if not a.get("accessControl"):
            access.append("NO STUDENT ACCESS")
        try:
            numbers[a.get("set")].append(int(a.get("number")))
        except (TypeError, ValueError):
            pass
        assessments.append(
            dict(
                instance=instance,
                dir=str(a_path.parent.relative_to(COURSE)).replace("\\", "/"),
                label=label,
                type=a.get("type"),
                set=a.get("set"),
                number=a.get("number"),
                title=a.get("title"),
                questions=qids,
                access=", ".join(access),
            )
        )

    questions = []
    for info_path in sorted((COURSE / "questions").rglob("info.json")):
        qdir = info_path.parent
        info = json.loads(info_path.read_text(encoding="utf-8"))
        html_path = qdir / "question.html"
        html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        qid = str(qdir.relative_to(COURSE / "questions")).replace("\\", "/")
        questions.append(
            dict(
                id=qid,
                title=info.get("title"),
                topic=info.get("topic"),
                tags=info.get("tags", []),
                format=question_format(info, html),
                used_in=used_in.get(qid, []),
            )
        )

    next_numbers = {s: (max(numbers.get(s, [0]) or [0]) + 1) for s in sorted(set(abbrev) | set(numbers))}
    data = dict(
        topics=[t["name"] for t in course.get("topics", [])],
        tags=[t["name"] for t in course.get("tags", [])],
        instances=sorted({p.parent.name for p in (COURSE / "courseInstances").rglob("infoCourseInstance.json")}),
        questions=questions,
        assessments=assessments,
        next_number=next_numbers,
    )
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
        return

    print(f"Course instances: {', '.join(data['instances'])}")
    print(f"Topics: {', '.join(data['topics'])}\n")
    print(f"QUESTION BANK ({len(questions)})")
    for q in questions:
        used = ", ".join(q["used_in"]) or "unused"
        print(f"  {q['id']:45s} {q['format']:16s} [{q['topic']}] {q['title']}  (tags: {', '.join(q['tags'])}; used in: {used})")
    print(f"\nASSESSMENTS ({len(assessments)})")
    for a in assessments:
        print(f"  {a['label']:6s} {a['type']:8s} {a['title']!s:40s} {len(a['questions'])} q  {a['dir']}  [{a['access']}]")
    print("\nNEXT FREE NUMBER: " + ", ".join(f"{s}={n}" for s, n in next_numbers.items() if s in ("Homework", "Quiz", "Exam")))


if __name__ == "__main__":
    main()
