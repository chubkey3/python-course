"""
stdin/stdout judge for PrairieLearn workspace questions.

Runs inside the `prairielearn/grader-python` image (as root) via run.sh.
For each test case in /grade/tests/cases.json it runs the student's program
(/grade/student/main.py by default) as the unprivileged `ag` user, feeds the
case's input on stdin, and compares stdout to the expected output.

cases.json format:

{
  "studentFile": "main.py",        # optional, default "main.py"
  "timeoutSeconds": 2,             # optional, per test case, default 2
  "compare": "tokens",             # optional: "tokens" (default), "lines", or "exact"
  "cases": [
    {
      "name": "Sample 1",          # optional, default "Test N"
      "input": "5\n",              # stdin given to the program
      "output": "120\n",           # expected stdout
      "points": 1,                 # optional, default 1
      "hidden": false              # optional, default true; hidden cases do not reveal input/expected output
    }
  ]
}

Compare modes:
  tokens - whitespace-insensitive: "1 2\n3" matches "1\n2\n3" (most forgiving; typical CP judge)
  lines  - line-by-line, ignoring trailing spaces and trailing blank lines
  exact  - byte-for-byte
"""

import json
import os
import pwd
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import traceback

GRADE_DIR = os.environ.get("JUDGE_GRADE_DIR", "/grade")  # override only for local testing
TESTS_FILE = os.path.join(GRADE_DIR, "tests", "cases.json")
STUDENT_DIR = os.path.join(GRADE_DIR, "student")
RESULTS_DIR = os.path.join(GRADE_DIR, "results")

SANDBOX_USER = "ag"
MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GiB address space
OUTPUT_LIMIT_BYTES = 8 * 1024 * 1024  # max bytes written to stdout/stderr files
MAX_PROCESSES = 64
SHOW_CHARS = 1500  # truncate displayed text to keep results.json small


def write_results(results: dict) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f)


def not_gradable(message: str) -> None:
    write_results({"gradable": False, "message": message, "format_errors": [message]})


def truncate(text: str, limit: int = SHOW_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text) - limit} more characters]"


def normalize(text: str, mode: str):
    text = text.replace("\r\n", "\n")
    if mode == "exact":
        return text
    if mode == "lines":
        lines = [line.rstrip() for line in text.split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        return lines
    return text.split()  # tokens


def limit_resources() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_LIMIT_BYTES, OUTPUT_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_NPROC, (MAX_PROCESSES, MAX_PROCESSES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run_case(cmd, cwd, env, user_kwargs, stdin_text, timeout):
    """Returns (status, stdout, stderr). status: ok | runtime_error | timeout | output_limit"""
    with (
        tempfile.TemporaryFile() as fin,
        tempfile.TemporaryFile() as fout,
        tempfile.TemporaryFile() as ferr,
    ):
        fin.write(stdin_text.encode("utf-8"))
        fin.seek(0)
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=fin,
            stdout=fout,
            stderr=ferr,
            start_new_session=True,
            preexec_fn=limit_resources,
            **user_kwargs,
        )
        status = "ok"
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            status = "timeout"
        # Kill the whole process group (also cleans up anything the program spawned).
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.wait()

        fout.seek(0)
        ferr.seek(0)
        stdout = fout.read(OUTPUT_LIMIT_BYTES).decode("utf-8", errors="replace")
        stderr = ferr.read(64 * 1024).decode("utf-8", errors="replace")

        if status == "ok":
            # Python ignores SIGXFSZ, so hitting RLIMIT_FSIZE shows up as "OSError: [Errno 27] File too large".
            if proc.returncode == -signal.SIGXFSZ or "[Errno 27]" in stderr:
                status = "output_limit"
            elif proc.returncode != 0:
                status = "runtime_error"
        return status, stdout, stderr


def main() -> None:
    try:
        with open(TESTS_FILE, encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        not_gradable(f"Autograder misconfigured (could not read tests/cases.json): {e}. Please contact course staff.")
        return

    student_file = config.get("studentFile", "main.py")
    timeout = float(config.get("timeoutSeconds", 2))
    compare = config.get("compare", "tokens")
    cases = config.get("cases", [])

    student_path = os.path.join(STUDENT_DIR, student_file)
    if not os.path.isfile(student_path):
        not_gradable(f"Could not find {student_file} in your workspace. Make sure the file exists and is saved.")
        return

    with open(student_path, encoding="utf-8", errors="replace") as f:
        source = f.read()
    if not source.strip():
        not_gradable(f"{student_file} is empty. Write your solution, save the file, then submit.")
        return
    try:
        compile(source, student_file, "exec")
    except SyntaxError as e:
        detail = "".join(traceback.format_exception_only(type(e), e))
        not_gradable(f"Your code has a syntax error, so it was not graded (this does not use up an attempt):\n{detail}")
        return

    # Copy the student's program into a fresh sandbox directory owned by the limited user.
    sandbox = tempfile.mkdtemp(prefix="judge-")
    shutil.copy(student_path, os.path.join(sandbox, student_file))

    user_kwargs = {}
    if os.geteuid() == 0:
        try:
            pw = pwd.getpwnam(SANDBOX_USER)
            for root, dirs, files in os.walk(sandbox):
                for name in dirs + files:
                    os.chown(os.path.join(root, name), pw.pw_uid, pw.pw_gid)
            os.chown(sandbox, pw.pw_uid, pw.pw_gid)
            user_kwargs = {"user": pw.pw_uid, "group": pw.pw_gid, "extra_groups": []}
            # Prevent student code from reading the test cases, reference solution, or data.
            os.chmod(GRADE_DIR, 0o700)
        except KeyError:
            pass  # no sandbox user in this image; run as current user

    env = {
        "PATH": "/venv/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME": sandbox,
        "LANG": "en_US.UTF-8",
        "PYTHONIOENCODING": "UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }
    cmd = [sys.executable, student_file]

    tests = []
    earned = 0.0
    total = 0.0
    passed = 0
    for i, case in enumerate(cases, start=1):
        name = case.get("name", f"Test {i}")
        points = float(case.get("points", 1))
        hidden = bool(case.get("hidden", True))
        stdin_text = case.get("input", "")
        expected = case.get("output", "")
        total += points

        status, stdout, stderr = run_case(cmd, sandbox, env, user_kwargs, stdin_text, timeout)

        ok = status == "ok" and normalize(stdout, compare) == normalize(expected, compare)
        if ok:
            earned += points
            passed += 1
            verdict = "Passed"
        elif status == "timeout":
            verdict = f"Time limit exceeded (more than {timeout:g} seconds). Check for an infinite loop or a missing input() call."
        elif status == "output_limit":
            verdict = "Output limit exceeded. Your program printed far too much (infinite loop?)."
        elif status == "runtime_error":
            verdict = "Runtime error (your program crashed)."
        else:
            verdict = "Wrong answer."

        message = verdict
        output = ""
        if not ok:
            if hidden:
                message += " (This is a hidden test case.)"
            else:
                output += f"Input:\n{truncate(stdin_text)}\n"
                output += f"Expected output:\n{truncate(expected)}\n"
                output += f"Your output:\n{truncate(stdout) if stdout else '(nothing printed)'}\n"
            if status == "runtime_error" and stderr:
                output += f"Error:\n{truncate(stderr.strip(), 1000)}\n"

        tests.append(
            {
                "name": name,
                "points": points if ok else 0,
                "max_points": points,
                "message": message,
                "output": output,
            }
        )

    shutil.rmtree(sandbox, ignore_errors=True)

    score = earned / total if total > 0 else 0.0
    write_results(
        {
            "gradable": True,
            "score": score,
            "message": f"Passed {passed} of {len(cases)} test cases.",
            "tests": tests,
        }
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        not_gradable("The autograder encountered an internal error. Please contact course staff.")
