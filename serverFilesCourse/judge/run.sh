#!/bin/bash
# Entrypoint for stdin/stdout-judged questions. Referenced from each question's
# info.json as externalGradingOptions.entrypoint.
PY=/venv/bin/python3
[ -x "$PY" ] || PY=python3
exec "$PY" /grade/serverFilesCourse/judge/judge.py
