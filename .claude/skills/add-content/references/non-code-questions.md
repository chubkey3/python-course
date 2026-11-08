# Non-code questions (concept checks)

These are graded inside PrairieLearn, with no external grader. They're good for "what does this code print?", "which of these loops…", or ordering a few lines of code. Keep them static (no `server.py`) unless the instructor asks for randomized numbers.

## Files

```
questions/<topic-folder>/<slug>/
  info.json
  question.html
  snippet.py      # optional: code shown with <pl-code source-file-name="snippet.py">
```

## info.json

```json
{
  "uuid": "<new uuid>",
  "title": "<Title>",
  "topic": "<a topic from infoCourse.json>",
  "tags": ["concept", "<tags from infoCourse.json>"],
  "type": "v3",
  "singleVariant": true
}
```

There's no `gradingMethod`; it defaults to Internal. Use the standard tag `concept` for conceptual checks and `MC` for multiple choice.

## Showing code

Put the code in `snippet.py` next to `question.html` and display it with:

```html
<pl-code language="python" source-file-name="snippet.py"></pl-code>
```

This avoids HTML-escaping problems with `<`, `>` and `&`. **Run the snippet with Python yourself** and use its real output as the correct answer. Never work out the output in your head.

## Templates

### Multiple choice: what does this print?

```html
<pl-question-panel>
  <p>What does this code print?</p>
  <pl-code language="python" source-file-name="snippet.py"></pl-code>
</pl-question-panel>

<pl-multiple-choice answers-name="output" weight="1">
  <pl-answer correct="true">10 7 4 1</pl-answer>
  <pl-answer correct="false">10 7 4 1 -2</pl-answer>
  <pl-answer correct="false">10 7 4</pl-answer>
  <pl-answer correct="false">7 4 1</pl-answer>
</pl-multiple-choice>
```

Make each distractor the output of a specific, common mistake (off-by-one, wrong stop value, wrong condition), not a random value. Order is randomized by default; set `order="fixed"` if the choices have a natural order.

### Checkbox: select all that apply

```html
<pl-question-panel>
  <p>Which of these calls <strong>change</strong> the list <code>nums</code>? Select all that apply.</p>
</pl-question-panel>

<pl-checkbox answers-name="mutating" weight="1" partial-credit="net-correct">
  <pl-answer correct="true"><code>nums.sort()</code></pl-answer>
  <pl-answer correct="false"><code>sorted(nums)</code></pl-answer>
  <pl-answer correct="true"><code>nums.append(3)</code></pl-answer>
  <pl-answer correct="false"><code>nums.count(3)</code></pl-answer>
</pl-checkbox>
```

### Integer answer

```html
<pl-question-panel>
  <p>What is the value of <code>total</code> after this code runs?</p>
  <pl-code language="python" source-file-name="snippet.py"></pl-code>
</pl-question-panel>

<pl-integer-input answers-name="total" label="<code>total</code> =" correct-answer="12"></pl-integer-input>
```

### Short text answer

```html
<pl-string-input answers-name="method" label="Method name:" correct-answer="append" remove-leading-trailing="true"></pl-string-input>
```

Use `ignore-case="true"` when case doesn't matter. Avoid string answers that have several valid spellings; use multiple choice for those.

### Put the lines of code in order

```html
<pl-question-panel>
  <p>Arrange the lines to print the sum of the even numbers in <code>nums</code>.</p>
</pl-question-panel>

<pl-order-blocks answers-name="code" format="code" code-language="python" indentation="true" grading-method="ordered">
  <pl-answer correct="true" indent="0">total = 0</pl-answer>
  <pl-answer correct="true" indent="0">for x in nums:</pl-answer>
  <pl-answer correct="true" indent="1">if x % 2 == 0:</pl-answer>
  <pl-answer correct="true" indent="2">total += x</pl-answer>
  <pl-answer correct="true" indent="0">print(total)</pl-answer>
  <pl-answer correct="false">for i in range(0, len(nums), 2):</pl-answer>
</pl-order-blocks>
```

Use `grading-method="dag"` with `tag`/`depends` when several orders are correct; see `docs/elements/pl-order-blocks.md` in the PrairieLearn repo, or the online docs.

## Points and attempts

- Homework: `"autoPoints": 2–5` is typical for a concept check. Students get unlimited tries, so a static question is effectively practice.
- Exam/quiz: use 1–2 attempts (`"autoPoints": 5` or `[5, 2]`). Many full-credit tries would let students guess their way through a multiple-choice question.

## Verification

`validate_course.py` checks the JSON, topics, tags and UUIDs. It can't check that the answer is right, so you must:
- run every snippet with `python snippet.py` and compare the output to the answer marked correct, and
- make sure each distractor really is wrong, by running it if it's code.
