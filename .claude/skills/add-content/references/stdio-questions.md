# stdin/stdout coding questions (workspace or in-browser editor)

Both formats use the course judge (`serverFilesCourse/judge/`). The student's `main.py` reads input with `input()` and prints the answer. The judge runs it once per case in `tests/cases.json` and scores it by the fraction of points passed. Look at `questions/loops-and-lists/sum-of-evens/` for a complete working example.

## Files

```
questions/<topic-folder>/<slug>/
  info.json
  question.html
  tests/cases.json        # test cases; hidden from students
  tests/solution.py       # reference solution; hidden from students
  workspace/main.py       # workspace format only: starter code
  workspace/sample_input.txt   # workspace format only: written by check_question.py --fix
  starter.py              # editor format only: starter code, loaded by <pl-file-editor source-file-name>
```

## info.json

Workspace format:

```json
{
  "uuid": "<new uuid>",
  "title": "<Title in sentence case>",
  "topic": "<a topic from infoCourse.json>",
  "tags": ["stdio", "<tags from infoCourse.json>"],
  "type": "v3",
  "singleVariant": true,
  "workspaceOptions": {
    "image": "prairielearn/workspace-vscode-python",
    "gradedFiles": ["main.py"]
  },
  "gradingMethod": "External",
  "externalGradingOptions": {
    "image": "prairielearn/grader-python",
    "entrypoint": "/grade/serverFilesCourse/judge/run.sh",
    "serverFilesCourse": ["judge/"],
    "timeout": 60
  }
}
```

Editor format: identical, but **remove `workspaceOptions`**. Keep `"singleVariant": true`, so a Homework retry doesn't reset the student's code to the starter.

## question.html

Workspace format:

```html
<pl-question-panel>
  <p>
    <statement: one or two short paragraphs>
  </p>
  <p><strong>Input:</strong> <exact format with constraints, e.g. the first line contains an integer $N$ ($1 \le N \le 1000$). Each of the next $N$ lines contains one integer.></p>
  <p><strong>Output:</strong> <exactly what to print></p>
  <!-- BEGIN SAMPLES (generated from tests/cases.json by tools/check_question.py --fix; edit cases.json, not this block) -->
  <!-- END SAMPLES -->

  <pl-workspace></pl-workspace>
</pl-question-panel>

<pl-submission-panel>
  <pl-external-grader-results></pl-external-grader-results>
  <pl-file-preview></pl-file-preview>
</pl-submission-panel>
```

Editor format: replace `<pl-workspace></pl-workspace>` with:

```html
  <pl-file-editor file-name="main.py" ace-mode="ace/mode/python" source-file-name="starter.py"></pl-file-editor>
```

Notes:
- Leave the samples block empty; `check_question.py --fix` fills it from the visible cases.
- Math goes in `$...$` (MathJax). Code identifiers go in `<code>`. Escape `<`, `>` and `&` as `&lt;`, `&gt;` and `&amp;`.
- Per the style guide, don't add paragraphs about how to write, test or submit code.

## tests/cases.json

```json
{
  "timeoutSeconds": 2,
  "compare": "tokens",
  "cases": [
    { "name": "Sample 1", "input": "5\n1\n2\n3\n4\n5\n", "output": "", "points": 1, "hidden": false,
      "explanation": "The even numbers are $2$ and $4$, and $2 + 4 = 6$." },
    { "name": "Hidden 1", "input": "4\n1\n3\n5\n7\n", "output": "", "points": 1, "hidden": true }
  ]
}
```

- Leave `output` empty; `--fix` fills it by running `tests/solution.py`. Every input must end with `\n`.
- `hidden: false` marks a sample. Samples appear in the statement, and failures show the student the input, expected output and actual output. Hidden cases reveal only the verdict.
- `explanation` (HTML allowed, samples only) is rendered under the sample in `question.html`.
- `compare`: `tokens` (default; whitespace-insensitive, so the line layout of the output doesn't matter), `lines` (when line structure matters, e.g. printing a grid), `exact` (rarely needed).
- Name cases `Sample 1..k` and `Hidden 1..m`. Students see the names, so never make a hidden name describe its input.

### Designing the tests

Samples: 1–2 typical cases that show the format. One of them should illustrate the main trap, e.g. even values vs. even indices.

Hidden tests (about 5–8), chosen by intent:
- **Boundaries:** the smallest input (N = 1, n = 0), values at the constraint limits.
- **Degenerate answers:** an answer of 0 (nothing matches), every element matching, all negatives.
- **Misconception traps:** inputs where the likely wrong solution gives a different answer. Think about what a beginner gets wrong: off-by-one in `range`, `>` vs `>=`, indices vs values, forgetting negatives, initializing the max to 0.
- **One large random case** at the top of the constraints. Generate it with a throwaway script with a fixed seed and paste the input into `cases.json`. Don't commit the generator.

Every case should be solvable by the simple intended solution within the time limit. If the solution itself needs more than about a second, the constraints are too big for this course.

## tests/solution.py

The simplest correct solution, written the way a student in this unit would write it, using only constructs from the topic. It's the source of truth for every expected output, so make it obviously correct.

## Starter code (workspace/main.py or starter.py)

```python
# <Title>
# <One or two lines restating the task: what to read, what to print.>
#
# Test:  python3 main.py < sample_input.txt

n = int(input())

# Write your code below
```

- Pre-write the `input()` lines for single values (`n`, `start`, `step`). Leave building lists from N lines to the student; that's part of the practice.
- For the editor format, change the test line to `# Click "Save & Grade" to run the tests.`, since there's no terminal.
- The starter must **not** pass the tests. `test_judge.py` checks this.

## Workflow recap

1. Write `info.json`, `question.html` (empty samples block), `tests/cases.json` (empty outputs), `tests/solution.py` and the starter.
2. Run `python tools/check_question.py questions/<topic-folder>/<slug> --fix`.
3. Read the regenerated samples in `question.html`. If an explanation no longer matches its sample output, fix the explanation in `cases.json` and run `--fix` again.
4. Run `python tools/test_judge.py questions/<topic-folder>/<slug>` (as part of step 6 in SKILL.md).
