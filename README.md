# Python: Competitive Programming in Python

PrairieLearn course for homework, quizzes, and exams. Students solve problems in a VS Code (Python) workspace, and their code is autograded with stdin/stdout tests, as in a programming contest.

## Layout

```
infoCourse.json                       course name/title, timezone, assessment sets (HW/Q/E), topics, tags
courseInstances/Ongoing/              the one (open-ended) course instance
  infoCourseInstance.json             published 2026-11-01 .. 2030-12-31
  assessments/quiz1/                  Q1: Loops, lists, and indexing (Exam-type, 90 min, 20 full-credit tries per question)
questions/<topic>/<question>/
  info.json                           metadata + workspace image + grader config
  question.html                       problem statement + <pl-workspace>
  workspace/main.py                   starter code copied into the student's workspace
  workspace/sample_input.txt          sample 1 input, so students can run: python3 main.py < sample_input.txt
  tests/cases.json                    test cases (hidden from students)
  tests/solution.py                   reference solution (hidden from students; used by tools/check_question.py)
serverFilesCourse/judge/              shared stdin/stdout judge used by every question
tools/check_question.py               local authoring helper
start-local.sh                        run PrairieLearn locally (from WSL) with workspaces + grading
```

## Running locally

Workspaces and external grading need Docker, run from a **WSL 2** shell:

1. Start Docker Desktop. Under Settings > Resources > WSL integration, enable your distro (Debian).
2. In a WSL shell, run `bash /mnt/c/Users/jason/python-course/start-local.sh`.
3. Open <http://localhost:3000/pl>. The course shows up as "Python". Open **Ongoing**, then **Q1**.
4. After editing any JSON file, click **Load from disk** in PrairieLearn.

The first workspace launch and the first grading job pull the `prairielearn/workspace-vscode-python` and `prairielearn/grader-python` images, which takes a few minutes.

## Adding a question

1. Copy an existing folder, e.g. `questions/loops-and-lists/factorial` -> `questions/<topic-folder>/<new-name>`.
2. In `info.json`, set a **new `uuid`** (PowerShell: `[guid]::NewGuid()`), a `title`, a `topic` (one of the topics in `infoCourse.json`), and `tags`.
3. Edit `question.html` (statement, input/output format, samples), `workspace/main.py` (starter code), and `tests/solution.py`.
4. In `tests/cases.json`, list the case inputs. Mark samples `"hidden": false`; mark the others `"hidden": true`. Then fill in the expected outputs from your solution and check them:
   ```
   python tools/check_question.py questions/<topic-folder>/<new-name> --fix
   python tools/check_question.py --all
   ```
5. Add it to an assessment's `zones[].questions` in `infoAssessment.json` using its ID (the path under `questions/`, e.g. `"loops-and-lists/factorial"`).

### `tests/cases.json`

```json
{
  "timeoutSeconds": 2,
  "compare": "tokens",
  "cases": [
    { "name": "Sample 1", "input": "5\n", "output": "120\n", "points": 1, "hidden": false },
    { "name": "Hidden 1", "input": "0\n", "output": "1\n", "points": 1, "hidden": true }
  ]
}
```

- `compare`: `tokens` (whitespace-insensitive, the default), `lines` (ignores trailing spaces and trailing blank lines), or `exact`.
- For a failed visible case, students see the input, the expected output, and their output. For a failed hidden case, they see only the verdict (wrong answer / runtime error / time limit), plus the error traceback if the program crashed.
- A syntax error or empty `main.py` is reported as "not gradable" and doesn't use up an attempt.
- The score is the fraction of points passed.

### How grading works

Each question's `info.json` sets `"gradingMethod": "External"` with the `prairielearn/grader-python` image and `entrypoint: /grade/serverFilesCourse/judge/run.sh`. When a student clicks **Save & Grade**, PrairieLearn copies `main.py` (listed in `workspaceOptions.gradedFiles`) out of the workspace. The judge then runs it once per test case as an unprivileged user, with a time limit, a 1 GiB memory limit, and an output limit. The test files are locked away from the student's process, so their code can't read them.

## Adding assessments

Create `courseInstances/Ongoing/assessments/<name>/infoAssessment.json` with a new `uuid`, a `type` (`Homework` or `Exam`), a `set` (`Homework` / `Quiz` / `Exam`), a `number`, a `title`, `zones`, and `accessControl`. You can also adjust access (release dates, time limits, passwords) on the assessment's **Access** page in the PrairieLearn UI. See `quiz1` for an example. Only Exam-type assessments support time limits.

## Moving to hosted PrairieLearn

1. Request a course space: in PrairieLearn, open the user menu and choose **Course Requests**.
2. When it's approved, you'll get a GitHub repository. Push this folder's contents to it, then click **Sync** in PrairieLearn.

## Notes

- `.gitattributes` forces LF line endings. Keep it: `run.sh` and test files run on Linux, and CRLF line endings break them.
- `singleVariant: true` is required for workspace questions, so a student's workspace isn't reset by new variants.
