# Assessments: presets, JSON, and the exam checklist

Assessments live in `courseInstances/Ongoing/assessments/<dir>/infoAssessment.json`. The course has one instance, `Ongoing`; check `course_index.py` in case more have been added since.

## Naming

| Set (`"set"`) | Label | Folder | `"type"` |
|---|---|---|---|
| `Homework` | HW1, HW2, … | `hw1`, `hw2`, … | `Homework` |
| `Quiz` | Q1, Q2, … | `quiz1`, `quiz2`, … | `Exam` (needed for time limits) |
| `Exam` | E1, E2, … | `exam1`, `exam2`, … | `Exam` |

`"number"` is a string (`"2"`). Take the next free number from `python tools/course_index.py`. The `title` is the topic, e.g. "List operations". PrairieLearn shows students "HW2: List operations".

## Homework preset (confirm with the instructor; always ask the due date)

- Homework-type: unlimited graded submissions. A workspace question keeps one variant, so the student's files are never reset.
- 10 points per question. Partial credit is the fraction of tests passed, and a better later submission adds the difference, so the best score effectively counts.
- Released immediately (today `T00:00:01`). The due date is asked; `null` means no due date.
- After the due date: no more submissions, but students can still review the questions. Confirm this part, since PrairieLearn's default hides the questions.

```json
{
  "uuid": "<new uuid>",
  "type": "Homework",
  "title": "<title>",
  "set": "Homework",
  "number": "<N>",
  "text": "<p>Write each solution in <code>main.py</code>: read input with <code>input()</code> and print the answer with <code>print()</code>. Test as often as you like, then click <strong>Save &amp; Grade</strong>. You can resubmit as many times as you want before the due date.</p>",
  "accessControl": [
    {
      "dateControl": {
        "release": { "date": "<YYYY-MM-DD>T00:00:01" },
        "due": { "date": "<YYYY-MM-DD>T23:59:59 or null>" }
      },
      "afterComplete": { "questions": { "hidden": false } }
    }
  ],
  "zones": [
    {
      "questions": [
        { "id": "<topic-folder>/<slug>", "autoPoints": 10 }
      ]
    }
  ]
}
```

Write the `text` so it fits the formats actually used. If an assessment has only in-browser-editor questions, say "in the editor" instead of mentioning a workspace. If it has non-code questions, a one-line text is enough.

Optional extras to offer only if relevant:
- **Late submissions:** add `"lateDeadlines": [{ "date": "...", "credit": 50 }]` inside `dateControl`. Credit must be below 100.
- **Practice after the deadline:** `"afterLastDeadline": { "allowSubmissions": true, "credit": 0 }`.

## Quiz preset (same as Q1; confirm with the instructor)

- Exam-type, released immediately, no due date, **90-minute** time limit once started.
- 10 points per question with **20 graded submissions, all for full credit**. In Exam-type assessments, the length of the `autoPoints` list is the number of attempts.
- Questions in the listed order (`shuffleQuestions: false`), no honor-code checkbox.

```json
{
  "uuid": "<new uuid>",
  "type": "Exam",
  "title": "<title>",
  "set": "Quiz",
  "number": "<N>",
  "text": "<p>Each question opens a VS Code workspace. Write your solution in <code>main.py</code>: read input with <code>input()</code> and print the answer with <code>print()</code>. You can test your code in the VS Code terminal with <code>python3 main.py</code> as often as you like. Click <strong>Save &amp; Grade</strong> on the question page to submit. Each question allows up to 20 graded submissions, all for full credit. You have 90 minutes once you start.</p>",
  "shuffleQuestions": false,
  "requireHonorCode": false,
  "accessControl": [
    {
      "dateControl": {
        "release": { "date": "<YYYY-MM-DD>T00:00:01" },
        "due": { "date": null },
        "durationMinutes": 90
      }
    }
  ],
  "zones": [
    {
      "questions": [
        { "id": "<topic-folder>/<slug>", "autoPoints": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10] }
      ]
    }
  ]
}
```

If the instructor changes the minutes or the number of tries, update the `text` to match.

## Exam checklist (no preset; ask every item)

Batch these into two AskUserQuestion calls of up to four questions each. Give sensible options, and mark one "(Recommended)" when there's a clear default.

1. **Window:** release date/time, and when submissions close (`due`). Exams usually have both, e.g. release `2026-12-10T09:00:00`, due `2026-12-10T11:00:00`.
2. **Time limit:** `durationMinutes` (e.g. 50, 90, 120), or none.
3. **Password:** `password` for proctored exams, or none.
4. **Attempts/points per question:** a single attempt (`"autoPoints": 10`), decreasing (`[10, 7, 4]`), or N full-credit tries (`[10, 10, 10, …]`). Coding questions usually deserve several tries. For non-code questions, use 1–2 tries so students can't guess their way through.
5. **Honor code:** `requireHonorCode` (default true for exams), with optional custom `honorCode` text.
6. **Order and titles:** `shuffleQuestions` (default true for Exam-type) and `showQuestionTitles` (default false for Exam-type).
7. **After completion:** whether students can see their questions (`afterComplete.questions.hidden`, optional `visibleFromDate`) and their score (`afterComplete.score.hidden`, optional `visibleFromDate`).
8. **Real-time grading:** `allowRealTimeGrading` (default true). With it off, students get no test feedback until the exam is graded at the end, which is unusual for coding exams.

Skeleton:

```json
{
  "uuid": "<new uuid>",
  "type": "Exam",
  "title": "<title>",
  "set": "Exam",
  "number": "<N>",
  "text": "<p>...</p>",
  "shuffleQuestions": true,
  "requireHonorCode": true,
  "accessControl": [
    {
      "dateControl": {
        "release": { "date": "2026-12-10T09:00:00" },
        "due": { "date": "2026-12-10T11:00:00" },
        "durationMinutes": 90,
        "password": "optional"
      },
      "afterComplete": {
        "questions": { "hidden": true, "visibleFromDate": "2026-12-17T00:00:01" },
        "score": { "hidden": false }
      }
    }
  ],
  "zones": [
    { "title": "optional zone title", "questions": [ { "id": "...", "autoPoints": [10, 7, 4] } ] }
  ]
}
```

## Access-control rules worth knowing

- With no `accessControl`, students have no access. Staff always have access, so they can preview.
- The first element is the defaults rule: no `uuid`, and when it has `dateControl` it needs `release`. `due.date: null` means no due date.
- Credits must strictly decrease over time. Late-deadline and after-last-deadline credit must be below 100.
- `afterComplete.questions.hidden: false` can't be combined with `visibleFromDate`/`visibleUntilDate`.
- Per-student or per-label accommodations (extra time, etc.) are easiest on the assessment's **Access** page in PrairieLearn. Mention this rather than writing override rules, unless the instructor asks for them.

## Adding questions to an existing assessment

- Append to the last zone's `questions`, or to a zone the instructor names. Copy the points scheme the existing questions use, unless the instructor wants something different.
- If the assessment is Exam-type (quizzes too), warn the instructor first: students who have already started won't get the new questions.
- If the `text` mentions a question count or a time limit, update it.
